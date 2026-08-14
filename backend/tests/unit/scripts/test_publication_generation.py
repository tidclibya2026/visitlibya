from __future__ import annotations

import copy
import hashlib
import json
import shutil
import socket
from pathlib import Path

import pytest

from scripts.publication_generation import (
    LEDGER_PATH,
    MANIFEST_PATH,
    NATURAL_INPUTS,
    NATURAL_OUTPUT,
    PROTECTED_OUTPUTS,
    REPOSITORY_ROOT,
    GenerationValidationError,
    generate_natural_bytes,
    generate_to_directory,
    load_manifest,
    replace_supported,
    validate_manifest,
    validate_phase_2,
    verify_protected,
)
from scripts.publication_governance import (
    BASELINE_CLASSIFICATION,
    BASELINE_PATH,
    POLICY_PATH,
    canonical_governed_bytes,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, set[str]]:
    root = tmp_path / "repository"
    paths = [
        POLICY_PATH,
        LEDGER_PATH,
        BASELINE_PATH,
        MANIFEST_PATH,
        *map(Path, PROTECTED_OUTPUTS),
        *map(Path, NATURAL_INPUTS),
    ]
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, destination)
    return root, {path.as_posix() for path in paths}


def snapshot(root: Path) -> dict[Path, bytes]:
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def natural_source(root: Path, index: int = 0) -> tuple[Path, dict]:
    path = root / NATURAL_INPUTS[index]
    return path, read_json(path)


def update_natural_contract(root: Path, records: list[dict]) -> None:
    manifest = read_json(root / MANIFEST_PATH)
    contract = manifest["protected_outputs"][0]["governed_inputs"][0]
    ids = [record["source_feature_id"] for record in records]
    contract["record_count"] = len(ids)
    contract["ordered_source_ids_sha256"] = hashlib.sha256(",".join(map(str, ids)).encode("ascii")).hexdigest()
    write_json(root / MANIFEST_PATH, manifest)


def test_manifest_schema_and_path_allowlist(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = load_manifest(root)
    validate_manifest(root, manifest, tracked_paths=tracked)
    assert [item["path"] for item in manifest["protected_outputs"]] == list(PROTECTED_OUTPUTS)


def test_deterministic_generation_is_byte_identical(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = validate_phase_2(root, tracked_paths=tracked)
    assert generate_natural_bytes(root, manifest) == canonical_governed_bytes(root / NATURAL_OUTPUT)


def test_repeat_generation_has_identical_hash(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = validate_phase_2(root, tracked_paths=tracked)
    first = generate_natural_bytes(root, manifest)
    second = generate_natural_bytes(root, manifest)
    assert hashlib.sha256(first).digest() == hashlib.sha256(second).digest()


def test_verification_mode_makes_no_writes(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    before = snapshot(root)
    verify_protected(root, tracked_paths=tracked)
    assert snapshot(root) == before


def test_direct_edit_causes_failure(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path = root / NATURAL_OUTPUT
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(GenerationValidationError, match="mismatch"):
        verify_protected(root, tracked_paths=tracked)


def test_count_mismatch_causes_failure(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = read_json(root / MANIFEST_PATH)
    manifest["protected_outputs"][0]["expected_record_count"] += 1
    write_json(root / MANIFEST_PATH, manifest)
    with pytest.raises(GenerationValidationError, match="baseline"):
        validate_phase_2(root, tracked_paths=tracked)


def test_duplicate_source_id_causes_failure(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path, payload = natural_source(root)
    payload["records"][1]["source_feature_id"] = payload["records"][0]["source_feature_id"]
    write_json(path, payload)
    with pytest.raises(GenerationValidationError, match="duplicate source IDs"):
        generate_natural_bytes(root, validate_phase_2(root, tracked_paths=tracked))


def test_missing_source_id_causes_failure(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path, payload = natural_source(root)
    payload["records"].pop()
    write_json(path, payload)
    with pytest.raises(GenerationValidationError, match="missing or unexpected"):
        generate_natural_bytes(root, validate_phase_2(root, tracked_paths=tracked))


def test_unexpected_source_id_causes_failure(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path, payload = natural_source(root)
    payload["records"][0]["source_feature_id"] = 999999
    write_json(path, payload)
    with pytest.raises(GenerationValidationError, match="missing, unexpected, or reordered"):
        generate_natural_bytes(root, validate_phase_2(root, tracked_paths=tracked))


@pytest.mark.parametrize("source_id", [832, 913])
def test_heritage_ids_are_rejected_from_natural_layer(
    repository: tuple[Path, set[str]], source_id: int
) -> None:
    root, tracked = repository
    path, payload = natural_source(root)
    payload["records"][0]["source_feature_id"] = source_id
    write_json(path, payload)
    with pytest.raises(GenerationValidationError, match="heritage-review IDs"):
        generate_natural_bytes(root, validate_phase_2(root, tracked_paths=tracked))


def test_ledger_remains_empty_and_has_no_approved_event(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    validate_phase_2(root, tracked_paths=tracked)
    assert (root / LEDGER_PATH).read_bytes() == b""


def test_any_ledger_event_is_rejected(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    (root / LEDGER_PATH).write_text('{"decision":"APPROVED"}\n', encoding="utf-8")
    with pytest.raises(GenerationValidationError, match="APPROVED|zero events"):
        validate_phase_2(root, tracked_paths=tracked)


def test_source_publication_approved_must_remain_false(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path, payload = natural_source(root)
    payload["records"][0]["publication_approved"] = True
    write_json(path, payload)
    with pytest.raises(GenerationValidationError, match="publication_approved"):
        validate_phase_2(root, tracked_paths=tracked)


def test_frontend_publication_approved_must_remain_false(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path = root / NATURAL_OUTPUT
    path.write_text(path.read_text(encoding="utf-8").replace('"publicationApproved": false', '"publicationApproved": true', 1), encoding="utf-8")
    with pytest.raises(GenerationValidationError, match="publicationApproved|mismatch"):
        validate_phase_2(root, tracked_paths=tracked)


def test_legacy_baseline_classification_is_not_approval(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = validate_phase_2(root, tracked_paths=tracked)
    assert all(item["governance_classification"] == BASELINE_CLASSIFICATION for item in manifest["protected_outputs"])


def test_unsupported_regeneration_declaration_fails_closed(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = read_json(root / MANIFEST_PATH)
    frozen = manifest["protected_outputs"][1]
    frozen["deterministic_regeneration_supported"] = True
    frozen["generator_identifier"] = "invented-generator"
    frozen["generator_version"] = 1
    write_json(root / MANIFEST_PATH, manifest)
    with pytest.raises(GenerationValidationError, match="unsupported deterministic generator"):
        validate_phase_2(root, tracked_paths=tracked)


def test_output_replacement_requires_explicit_guard(repository: tuple[Path, set[str]]) -> None:
    root, _ = repository
    before = snapshot(root)
    with pytest.raises(GenerationValidationError, match="requires --allow-protected-replacement"):
        replace_supported(root, allow_protected_replacement=False)
    assert snapshot(root) == before


def test_generation_requires_no_network(
    repository: tuple[Path, set[str]], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, tracked = repository
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network used")))
    outputs = generate_to_directory(root, tmp_path / "generated", tracked_paths=tracked)
    assert len(outputs) == 1


def test_arabic_and_utf8_serialization_are_stable(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    raw = generate_natural_bytes(root, validate_phase_2(root, tracked_paths=tracked))
    assert "الجبل الأخضر".encode("utf-8") in raw
    assert b"\\u0627" not in raw
    assert raw.startswith(b"// Generated") and raw.endswith(b"\n")
    assert b"\r\n" not in raw and b"\r" not in raw


def test_generate_writes_only_to_external_output_directory(
    repository: tuple[Path, set[str]], tmp_path: Path
) -> None:
    root, tracked = repository
    before = snapshot(root)
    outputs = generate_to_directory(root, tmp_path / "generated", tracked_paths=tracked)
    assert outputs[0].read_bytes() == canonical_governed_bytes(root / NATURAL_OUTPUT)
    assert snapshot(root) == before


def test_protected_artifacts_remain_byte_identical(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    before = {path: (root / path).read_bytes() for path in PROTECTED_OUTPUTS}
    verify_protected(root, tracked_paths=tracked)
    assert {path: (root / path).read_bytes() for path in PROTECTED_OUTPUTS} == before


def test_guarded_replacement_is_noop_for_git_crlf_checkout(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    path = root / NATURAL_OUTPUT
    path.write_bytes(canonical_governed_bytes(path).replace(b"\n", b"\r\n"))
    before = path.read_bytes()
    assert replace_supported(root, allow_protected_replacement=True, tracked_paths=tracked) == []
    assert path.read_bytes() == before


def test_all_protected_counts_and_frozen_status(repository: tuple[Path, set[str]]) -> None:
    root, tracked = repository
    manifest = validate_phase_2(root, tracked_paths=tracked)
    assert [item["expected_record_count"] for item in manifest["protected_outputs"]] == [249, 12, 13]
    assert [item["deterministic_regeneration_supported"] for item in manifest["protected_outputs"]] == [True, False, False]
