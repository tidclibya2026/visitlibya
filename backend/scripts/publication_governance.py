"""Read-only validation for Publication Approval Governance Foundation Phase 1."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = Path("backend/data/governance/publication-policy.json")
LEDGER_PATH = Path("backend/data/governance/publication-approval-ledger.jsonl")
BASELINE_PATH = Path("backend/data/governance/legacy-publication-baseline.json")

GOVERNANCE_OWNER = "Tourism Information and Documentation Center"
LIFECYCLE_STATES = [
    "DRAFT", "REVIEW_REQUIRED", "UNDER_REVIEW", "RECOMMENDED", "APPROVED",
    "REJECTED", "DEFERRED", "EXPIRED", "REVOKED", "SUPERSEDED",
    "CORRECTION_REQUIRED",
]
DECISION_TYPES = [
    "CANONICAL_IDENTITY", "COORDINATE", "DESTINATION_MEMBERSHIP",
    "MEDIA_RIGHTS", "PUBLICATION", "REVOCATION", "CORRECTION",
]
INSTITUTIONAL_ROLES = [
    "data_preparer", "technical_validator", "subject_matter_reviewer",
    "media_rights_reviewer", "publication_approver", "final_release_operator",
    "auditor", "emergency_revocation_authority",
]
SEPARATION_RULES = [
    "A data preparer cannot approve the same subject and version.",
    "A publication approver cannot operate the final release for the same release.",
    "Technical validation cannot substitute for subject review.",
    "Media-rights approval remains independent.",
    "A release operator cannot override failed eligibility.",
    "An auditor cannot create or alter approval events through the validator.",
]
BASELINE_ARTIFACTS = {
    "assets/js/data/natural-tourism-layers.js": (
        "STATIC_NATURAL_TOURISM_FRONTEND_DATA", "NATURAL_FEATURES"
    ),
    "assets/js/data/curated-destinations.js": (
        "STATIC_CURATED_DESTINATION_FRONTEND_DATA", "CURATED_DESTINATIONS"
    ),
    "backend/data/dev/destinations.json": (
        "DEVELOPMENT_BACKEND_DESTINATION_SEED_DATA", "BACKEND_DESTINATIONS"
    ),
}
BASELINE_CLASSIFICATION = "LEGACY_PUBLIC_BASELINE_NOT_INSTITUTIONAL_APPROVAL"

POLICY_KEYS = {
    "schema_version", "policy_id", "policy_version", "governance_owner",
    "compatibility_mode", "canonicalization", "lifecycle_states",
    "decision_types", "institutional_roles", "separation_of_duties",
    "prerequisite_decisions", "legacy_baseline_policy", "append_only_policy",
    "invalidation_policy", "revocation_policy", "public_projection_policy",
    "release_policy",
}
BASELINE_KEYS = {
    "schema_version", "baseline_id", "artifact_status", "policy_reference",
    "created_from_commit", "artifacts", "summary", "policy",
}
BASELINE_ARTIFACT_KEYS = {
    "path", "sha256", "byte_size", "git_tracked", "semantic_role",
    "record_count", "count_semantics", "compatibility_classification",
}
FORBIDDEN_DATA_KEYS = {
    "personal_name", "person_name", "email", "personal_email", "password",
    "secret", "token", "access_token", "private_key", "private_evidence",
    "actor_name", "personal_actor_id",
}
SECRET_VALUE_PATTERN = re.compile(
    r"(?:gh[opusr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]+|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@)",
    re.IGNORECASE,
)


class GovernanceValidationError(ValueError):
    """A Phase 1 governance invariant was violated."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise GovernanceValidationError(f"BOM is not permitted: {path}")
        payload = json.loads(raw.decode("utf-8"))
    except GovernanceValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GovernanceValidationError(f"cannot read valid UTF-8 JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GovernanceValidationError(f"JSON root must be an object: {path}")
    return payload


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise GovernanceValidationError(
            f"{label} keys differ; missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}"
        )


def _require_exact(value: Any, expected: Any, label: str) -> None:
    if value != expected:
        raise GovernanceValidationError(f"{label} does not match the Phase 1 contract")


def _scan_sensitive(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in FORBIDDEN_DATA_KEYS:
                raise GovernanceValidationError(f"personal or secret-like field is prohibited: {path}.{key}")
            _scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        raise GovernanceValidationError(f"secret-like value is prohibited: {path}")


def validate_policy(policy: dict[str, Any]) -> None:
    _scan_sensitive(policy, "policy")
    _exact_keys(policy, POLICY_KEYS, "policy")
    _require_exact(policy["schema_version"], 1, "policy schema_version")
    _require_exact(policy["policy_id"], "visit-libya-publication-approval-governance", "policy_id")
    _require_exact(policy["policy_version"], "1.0.0-phase-1", "policy_version")
    _require_exact(policy["governance_owner"], GOVERNANCE_OWNER, "governance_owner")
    _require_exact(policy["lifecycle_states"], LIFECYCLE_STATES, "lifecycle_states")
    _require_exact(policy["decision_types"], DECISION_TYPES, "decision_types")
    _require_exact(policy["institutional_roles"], INSTITUTIONAL_ROLES, "institutional_roles")
    _require_exact(policy["separation_of_duties"], SEPARATION_RULES, "separation_of_duties")

    compatibility = policy["compatibility_mode"]
    required_compatibility = {
        "phase": "FOUNDATION_PHASE_1_VALIDATION_ONLY",
        "current_behavior": "Current static and backend publication behavior remains unchanged in Phase 1.",
        "legacy_freeze": "Legacy content is frozen as an explicit baseline.",
        "approval_disclaimer": "Legacy baseline status is not institutional approval.",
        "future_content_rule": "No new or changed public record may be treated as institutionally approved without a future valid ledger decision.",
        "compatibility_field_rule": "publication_approved remains compatibility metadata and is not authoritative.",
        "empty_ledger_rule": "An empty ledger means no governed approvals exist.",
    }
    _require_exact(compatibility, required_compatibility, "compatibility_mode")

    canonicalization = policy["canonicalization"]
    required_canonical = {
        "contract_version": 1,
        "encoding": "UTF-8",
        "key_ordering": "DETERMINISTIC_LEXICOGRAPHIC",
        "field_allowlist_policy": "VERSIONED_BY_SUBJECT_TYPE",
        "stable_number_representation": True,
        "include_visitor_visible_bilingual_fields": True,
        "include_source_ids": True,
        "include_authoritative_coordinates": True,
        "include_applicable_media_hashes": True,
        "exclude_approval_metadata": True,
        "digest_algorithm": "SHA-256",
        "digest_encoding": "LOWERCASE_HEXADECIMAL",
    }
    for key, expected in required_canonical.items():
        _require_exact(canonicalization.get(key), expected, f"canonicalization.{key}")
    allowlists = canonicalization.get("subject_type_field_allowlists")
    if not isinstance(allowlists, dict) or set(allowlists) != {"gis_feature", "destination", "media_asset"}:
        raise GovernanceValidationError("canonicalization subject-type field allowlists are invalid")
    if any(not isinstance(fields, list) or not fields or len(fields) != len(set(fields)) for fields in allowlists.values()):
        raise GovernanceValidationError("canonicalization field allowlists must be non-empty and unique")

    required_true_sections = {
        "prerequisite_decisions": {
            "publication_does_not_imply_other_approvals", "canonical_identity_independent",
            "coordinate_independent", "destination_membership_independent",
            "media_rights_independent", "publication_requires_applicable_active_prerequisites",
        },
        "legacy_baseline_policy": {
            "frozen_compatibility_evidence_only", "not_publication_approval",
            "not_identity_approval", "not_media_approval", "not_permission_for_new_content",
            "hash_mismatch_requires_explicit_review",
            "entry_removal_or_modification_prohibited_in_phase_1",
            "current_runtime_behavior_unchanged",
        },
        "invalidation_policy": {
            "approval_binds_to_exact_subject_content_hash",
            "content_change_invalidates_or_suspends_approval", "media_change_requires_recalculation",
            "approval_metadata_excluded_from_subject_hash",
        },
        "revocation_policy": {
            "revocation_requires_append_only_event", "reason_and_effective_date_required",
            "prior_events_retained", "emergency_takedown_requires_follow_up_audit",
        },
        "public_projection_policy": {
            "frontend_must_not_receive_personal_actor_data",
            "frontend_must_not_receive_private_evidence",
            "frontend_must_not_receive_secrets_or_tokens",
            "future_public_data_must_be_generated_from_governed_authoritative_data",
        },
        "release_policy": {
            "phase_1_static_deployment_behavior_unchanged",
            "release_operator_cannot_create_content_approval",
            "failed_validation_cannot_be_overridden_by_release_operator",
            "future_release_manifest_must_bind_governance_and_content_hashes",
        },
    }
    for section, required in required_true_sections.items():
        value = policy.get(section)
        if not isinstance(value, dict) or any(value.get(key) is not True for key in required):
            raise GovernanceValidationError(f"{section} weakens a required governance rule")
    if policy["public_projection_policy"].get("phase_1_frontend_generation_enabled") is not False:
        raise GovernanceValidationError("Phase 1 frontend generation must remain disabled")
    append_only = policy["append_only_policy"]
    _require_exact(append_only.get("ledger_format"), "UTF-8_JSON_LINES", "ledger format")
    _require_exact(append_only.get("phase_1_required_event_count"), 0, "Phase 1 ledger count")
    for key in ("existing_events_may_not_be_modified_deleted_or_reordered", "corrections_require_new_superseding_events", "validator_is_read_only"):
        if append_only.get(key) is not True:
            raise GovernanceValidationError(f"append_only_policy.{key} must be true")
    legacy = policy["legacy_baseline_policy"]
    _require_exact(legacy.get("classification"), BASELINE_CLASSIFICATION, "legacy classification")


def parse_phase_1_ledger(raw: bytes) -> list[dict[str, Any]]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise GovernanceValidationError("ledger must not contain a BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise GovernanceValidationError("ledger must be valid UTF-8") from exc
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GovernanceValidationError(f"ledger line {line_number} is invalid JSON") from exc
        if not isinstance(event, dict):
            raise GovernanceValidationError(f"ledger line {line_number} must be an object")
        _scan_sensitive(event, f"ledger[{line_number}]")
        events.append(event)
    if events:
        decisions = [str(event.get("decision", "UNKNOWN")) for event in events]
        if "APPROVED" in decisions:
            raise GovernanceValidationError("APPROVED events are prohibited in Phase 1")
        raise GovernanceValidationError("the Phase 1 ledger must contain zero events")
    return events


def canonical_governed_bytes(path: Path) -> bytes:
    """Return the exact LF Git representation of a governed UTF-8 text artifact."""
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GovernanceValidationError(f"governed artifact is not valid UTF-8: {path}") from exc
    canonical = raw.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        raise GovernanceValidationError(f"governed artifact contains a lone carriage return: {path}")
    return canonical


def _measure_count(path: Path, semantics: str) -> int:
    text = canonical_governed_bytes(path).decode("utf-8")
    if semantics == "NATURAL_FEATURES":
        count = len(re.findall(r'"sourceFeatureId"\s*:', text))
        declared = [int(value) for value in re.findall(r'"featureCount"\s*:\s*(\d+)', text)]
        if not declared or sum(declared) != count:
            raise GovernanceValidationError("natural frontend declared feature counts are inconsistent")
        return count
    if semantics == "CURATED_DESTINATIONS":
        return len(re.findall(r'^\s*slug:\s*"[a-z0-9-]+",\s*$', text, re.MULTILINE))
    if semantics == "BACKEND_DESTINATIONS":
        payload = json.loads(text)
        records = payload.get("records")
        if not isinstance(records, list):
            raise GovernanceValidationError("backend destination records are missing")
        return len(records)
    raise GovernanceValidationError(f"unsupported baseline count semantics: {semantics}")


def validate_baseline(
    root: Path,
    baseline: dict[str, Any],
    tracked_paths: set[str],
) -> None:
    _scan_sensitive(baseline, "baseline")
    _exact_keys(baseline, BASELINE_KEYS, "baseline")
    _require_exact(baseline["schema_version"], 1, "baseline schema_version")
    _require_exact(baseline["baseline_id"], "visit-libya-legacy-publication-baseline-phase-1", "baseline_id")
    _require_exact(
        baseline["artifact_status"],
        "FROZEN_COMPATIBILITY_EVIDENCE_NOT_INSTITUTIONAL_APPROVAL",
        "baseline artifact_status",
    )
    _require_exact(
        baseline["policy_reference"],
        "backend/data/governance/publication-policy.json#1.0.0-phase-1",
        "baseline policy_reference",
    )
    commit = baseline["created_from_commit"]
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise GovernanceValidationError("created_from_commit must be a full lowercase Git SHA")
    artifacts = baseline["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        raise GovernanceValidationError("baseline must contain exactly three artifacts")
    paths = [item.get("path") for item in artifacts if isinstance(item, dict)]
    if set(paths) != set(BASELINE_ARTIFACTS) or len(paths) != len(set(paths)):
        raise GovernanceValidationError("baseline artifact inventory is incomplete or duplicated")
    measured: dict[str, int] = {}
    for item in artifacts:
        path_text = item["path"]
        _exact_keys(item, BASELINE_ARTIFACT_KEYS, f"baseline artifact {path_text}")
        role, semantics = BASELINE_ARTIFACTS[path_text]
        _require_exact(item["semantic_role"], role, f"{path_text} semantic_role")
        _require_exact(item["count_semantics"], semantics, f"{path_text} count_semantics")
        _require_exact(item["compatibility_classification"], BASELINE_CLASSIFICATION, f"{path_text} classification")
        if item["git_tracked"] is not True or path_text not in tracked_paths:
            raise GovernanceValidationError(f"baseline artifact is not tracked: {path_text}")
        path = root / path_text
        if not path.is_file():
            raise GovernanceValidationError(f"baseline artifact is missing: {path_text}")
        canonical = canonical_governed_bytes(path)
        if item["byte_size"] != len(canonical):
            raise GovernanceValidationError(f"baseline byte-size mismatch: {path_text}")
        if item["sha256"] != hashlib.sha256(canonical).hexdigest():
            raise GovernanceValidationError(f"baseline SHA-256 mismatch: {path_text}")
        count = _measure_count(path, semantics)
        if item["record_count"] != count:
            raise GovernanceValidationError(f"baseline record-count mismatch: {path_text}")
        measured[semantics] = count
    expected_summary = {
        "artifact_count": 3,
        "natural_feature_count": measured["NATURAL_FEATURES"],
        "curated_frontend_destination_count": measured["CURATED_DESTINATIONS"],
        "backend_destination_count": measured["BACKEND_DESTINATIONS"],
        "governed_approval_event_count": 0,
    }
    _require_exact(baseline["summary"], expected_summary, "baseline summary")
    required_policy = {
        "frozen_compatibility_evidence_only": True,
        "not_publication_approval": True,
        "not_identity_approval": True,
        "not_media_approval": True,
        "not_permission_for_new_content": True,
        "hash_mismatch_requires_explicit_review": True,
        "entry_removal_or_modification_prohibited_in_phase_1": True,
        "current_runtime_behavior_unchanged": True,
    }
    _require_exact(baseline["policy"], required_policy, "baseline policy")


def _walk_named(value: Any, key_name: str) -> Iterable[Any]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == key_name:
                yield child
            yield from _walk_named(child, key_name)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_named(child, key_name)


def validate_approval_states(root: Path, tracked_paths: set[str]) -> None:
    gis_paths = sorted(
        path for path in tracked_paths
        if path.startswith("backend/data/gis/") and path.endswith(".json")
    )
    for relative in gis_paths:
        try:
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GovernanceValidationError(f"tracked GIS JSON cannot be validated: {relative}") from exc
        for value in _walk_named(payload, "publication_approved"):
            if isinstance(value, bool):
                if value is not False:
                    raise GovernanceValidationError(f"publication_approved became true: {relative}")
            elif isinstance(value, int):
                if value != 0:
                    raise GovernanceValidationError(f"publication_approved summary became nonzero: {relative}")
            else:
                raise GovernanceValidationError(f"publication_approved has unsupported value: {relative}")

    frontend = root / "assets/js/data/natural-tourism-layers.js"
    text = frontend.read_text(encoding="utf-8")
    values = re.findall(r'"publicationApproved"\s*:\s*([^,\r\n}]+)', text)
    if not values or any(value.strip() != "false" for value in values):
        raise GovernanceValidationError("natural frontend publicationApproved must remain false")


def _git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=root, input=input_bytes,
        capture_output=True, check=False,
    )


def _tracked_paths(root: Path) -> set[str]:
    result = _git(root, "ls-files", "-z")
    if result.returncode != 0:
        raise GovernanceValidationError("git ls-files failed")
    return {item for item in result.stdout.decode("utf-8").split("\0") if item}


def validate_repository(
    root: Path = REPOSITORY_ROOT,
    *,
    tracked_paths: set[str] | None = None,
    enforce_git: bool = True,
) -> None:
    policy = _load_json(root / POLICY_PATH)
    baseline = _load_json(root / BASELINE_PATH)
    try:
        ledger_raw = (root / LEDGER_PATH).read_bytes()
    except OSError as exc:
        raise GovernanceValidationError("publication approval ledger is missing") from exc
    validate_policy(policy)
    events = parse_phase_1_ledger(ledger_raw)
    if events:
        raise GovernanceValidationError("Phase 1 has governed approval events")
    tracked = tracked_paths if tracked_paths is not None else _tracked_paths(root)
    validate_baseline(root, baseline, tracked)
    validate_approval_states(root, tracked)

    if enforce_git:
        commit = baseline["created_from_commit"]
        if _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            raise GovernanceValidationError("baseline created_from_commit is not available")
        diff = _git(root, "diff", "--quiet", "HEAD", "--", *BASELINE_ARTIFACTS)
        if diff.returncode != 0:
            raise GovernanceValidationError("an existing public baseline artifact has working-tree or index changes")


def main() -> int:
    try:
        validate_repository()
    except GovernanceValidationError as exc:
        print(f"FAIL publication governance: {exc}", file=sys.stderr)
        return 1
    print("PASS publication governance Phase 1: policy valid; ledger empty; 3 legacy artifacts frozen; approvals unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
