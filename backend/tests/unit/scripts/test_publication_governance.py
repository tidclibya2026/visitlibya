from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.publication_governance import (
    BASELINE_ARTIFACTS,
    BASELINE_PATH,
    LEDGER_PATH,
    POLICY_PATH,
    REPOSITORY_ROOT,
    GovernanceValidationError,
    parse_phase_1_ledger,
    validate_repository,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def foundation(tmp_path: Path) -> tuple[Path, set[str]]:
    copied = [POLICY_PATH, LEDGER_PATH, BASELINE_PATH, *map(Path, BASELINE_ARTIFACTS)]
    for relative in copied:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, target)
    gis = Path("backend/data/gis/phase-1-test.json")
    (tmp_path / gis).parent.mkdir(parents=True, exist_ok=True)
    write_json(tmp_path / gis, {"records": [{"publication_approved": False}]})
    tracked = {path.as_posix() for path in copied} | {gis.as_posix()}
    return tmp_path, tracked


def validate(root: Path, tracked: set[str]) -> None:
    validate_repository(root, tracked_paths=tracked, enforce_git=False)


def test_valid_phase_1_policy_ledger_and_baseline(foundation: tuple[Path, set[str]]) -> None:
    validate(*foundation)


def test_empty_ledger_is_accepted() -> None:
    assert parse_phase_1_ledger(b"") == []


def test_any_event_is_rejected_during_phase_1() -> None:
    with pytest.raises(GovernanceValidationError, match="zero events"):
        parse_phase_1_ledger(b'{"decision":"REJECTED"}\n')


def test_approved_event_is_rejected_explicitly() -> None:
    with pytest.raises(GovernanceValidationError, match="APPROVED"):
        parse_phase_1_ledger(b'{"decision":"APPROVED"}\n')


def test_invalid_jsonl_is_rejected() -> None:
    with pytest.raises(GovernanceValidationError, match="invalid JSON"):
        parse_phase_1_ledger(b'{broken}\n')


def test_unsupported_policy_version_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy["policy_version"] = "2.0.0"
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="policy_version"):
        validate(root, tracked)


def test_unknown_lifecycle_state_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy["lifecycle_states"].append("UNKNOWN")
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="lifecycle_states"):
        validate(root, tracked)


def test_missing_institutional_role_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy["institutional_roles"].remove("publication_approver")
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="institutional_roles"):
        validate(root, tracked)


def test_weakened_separation_rule_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy["separation_of_duties"][0] = "A preparer may approve."
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="separation_of_duties"):
        validate(root, tracked)


def test_invalid_canonicalization_contract_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy["canonicalization"]["stable_number_representation"] = False
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="canonicalization"):
        validate(root, tracked)


def test_missing_baseline_artifact_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    (root / "assets/js/data/curated-destinations.js").unlink()
    with pytest.raises(GovernanceValidationError, match="missing"):
        validate(root, tracked)


def test_untracked_baseline_artifact_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    tracked.remove("assets/js/data/curated-destinations.js")
    with pytest.raises(GovernanceValidationError, match="not tracked"):
        validate(root, tracked)


def test_hash_mismatch_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    baseline = read_json(root / BASELINE_PATH)
    baseline["artifacts"][0]["sha256"] = "0" * 64
    write_json(root / BASELINE_PATH, baseline)
    with pytest.raises(GovernanceValidationError, match="SHA-256"):
        validate(root, tracked)


def test_byte_size_mismatch_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    baseline = read_json(root / BASELINE_PATH)
    baseline["artifacts"][0]["byte_size"] += 1
    write_json(root / BASELINE_PATH, baseline)
    with pytest.raises(GovernanceValidationError, match="byte-size"):
        validate(root, tracked)


def test_record_count_mismatch_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    baseline = read_json(root / BASELINE_PATH)
    baseline["artifacts"][0]["record_count"] += 1
    write_json(root / BASELINE_PATH, baseline)
    with pytest.raises(GovernanceValidationError, match="record-count"):
        validate(root, tracked)


def test_baseline_approval_claim_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    baseline = read_json(root / BASELINE_PATH)
    baseline["artifacts"][0]["compatibility_classification"] = "INSTITUTIONALLY_APPROVED"
    write_json(root / BASELINE_PATH, baseline)
    with pytest.raises(GovernanceValidationError, match="classification"):
        validate(root, tracked)


def test_publication_approved_true_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    write_json(root / "backend/data/gis/phase-1-test.json", {"publication_approved": True})
    with pytest.raises(GovernanceValidationError, match="became true"):
        validate(root, tracked)


def test_frontend_publication_approved_true_is_rejected(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    path = root / "assets/js/data/natural-tourism-layers.js"
    text = path.read_text(encoding="utf-8").replace('"publicationApproved": false', '"publicationApproved": true', 1)
    path.write_text(text, encoding="utf-8")
    baseline = read_json(root / BASELINE_PATH)
    item = next(entry for entry in baseline["artifacts"] if entry["path"] == "assets/js/data/natural-tourism-layers.js")
    raw = path.read_bytes()
    item["sha256"] = hashlib.sha256(raw).hexdigest()
    item["byte_size"] = len(raw)
    write_json(root / BASELINE_PATH, baseline)
    with pytest.raises(GovernanceValidationError, match="publicationApproved"):
        validate(root, tracked)


@pytest.mark.parametrize(
    "field,value",
    [("personal_name", "Person"), ("secret", "not-for-public-use"), ("token", "not-for-public-use")],
)
def test_personal_actor_or_secret_like_data_is_rejected(
    foundation: tuple[Path, set[str]], field: str, value: str
) -> None:
    root, tracked = foundation
    policy = read_json(root / POLICY_PATH)
    policy[field] = value
    write_json(root / POLICY_PATH, policy)
    with pytest.raises(GovernanceValidationError, match="prohibited"):
        validate(root, tracked)


def test_validation_makes_no_writes(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    validate(root, tracked)
    after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert after == before


def test_repeated_validation_is_deterministic(foundation: tuple[Path, set[str]]) -> None:
    root, tracked = foundation
    validate(root, tracked)
    first = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    validate(root, tracked)
    second = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert first == second
