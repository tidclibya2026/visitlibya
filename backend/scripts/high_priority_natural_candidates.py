#!/usr/bin/env python3
"""Build and validate the governed high-priority natural-candidate review packet."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT / "backend/data/gis/high-priority-natural-candidates.institutional-review.json"
INPUT_RELATIVE = "backend/data/gis/phase1-natural-editorial-candidates.review.json"
INPUT_SHA256 = "a04e40ec70051e6fb19f2b1a4002cf6d0b161eb7071e8aa56d5ad82fa4e2ba07"
EXTERNAL_HASHES = {
    "high-priority-natural-candidates.review.json": "4f6725b67ce91be836de44566790823893a61e11457eefed562cbe43ae99d458",
    "high-priority-natural-candidates-review.md": "760bf4ce1d85664c98a71d521cafb7d135a31f500a939d806d74bc124b562f24",
    "validate_high_priority_natural_candidates.py": "d7cc97590e45b68fcc10bf3e8d3a2a56ad2e4c4cd36150c8dc4e24061a7d3f31",
    "high-priority-natural-candidates-hashes.json": "615877480fd7795e60a92b4ced15fe5be42a4ded519f2b66742fdbee7f21bad0",
}
CATEGORY_ORDER = (
    "NATURAL_SPRINGS", "DAMS_AND_RESERVOIRS_REVIEW", "CAVES_AND_ROCK_FORMATIONS",
    "ISLANDS", "VALLEYS_AND_WADIS",
)
EXPECTED_ORDINAL_ORDER = (770, 817, 640, 80, 849, 938, 182)
EXPECTED_ACTIONS = {
    80: "RETURN_FOR_IDENTITY_REVIEW",
    182: "RETURN_FOR_IDENTITY_REVIEW",
    640: "ACCEPT_FOR_FIELD_VERIFICATION",
    770: "RETURN_FOR_DESCRIPTION",
    817: "ACCEPT_FOR_FIELD_VERIFICATION",
    849: "ACCEPT_FOR_FIELD_VERIFICATION",
    938: "RETURN_FOR_DESCRIPTION",
}
EXPECTED_DECISIONS = {
    "ACCEPT_FOR_FIELD_VERIFICATION": 3,
    "RETURN_FOR_DESCRIPTION": 2,
    "RETURN_FOR_IDENTITY_REVIEW": 2,
}
EXPECTED_CATEGORIES = {
    "NATURAL_SPRINGS": 2,
    "DAMS_AND_RESERVOIRS_REVIEW": 1,
    "CAVES_AND_ROCK_FORMATIONS": 1,
    "ISLANDS": 2,
    "VALLEYS_AND_WADIS": 1,
}
FALSE_FIELDS = (
    "publication_approved", "canonical_approval", "public_visibility_enabled",
    "publication_media_eligible", "editorial_selection_is_approval",
)
GOVERNANCE = {
    "publication_approved": False,
    "canonical_approval": False,
    "public_visibility_enabled": False,
    "publication_media_eligible": False,
    "institutional_review_status": "UNRESOLVED",
    "institutional_decision": "PENDING",
    "canonical_destination": None,
    "editorial_selection_is_approval": False,
}
ROUTING_REQUIREMENTS = {
    80: {
        "review_routing_action": "RETURN_FOR_IDENTITY_REVIEW",
        "cave_identity_confirmation_required": True,
        "archaeological_association_review_required": True,
        "rock_art_association_review_required": True,
        "mining_or_artificial_excavation_review_required": True,
        "publication_remains_prohibited": True,
    },
    182: {
        "review_routing_action": "RETURN_FOR_IDENTITY_REVIEW",
        "valley_identity_confirmation_required": True,
        "locality_confirmation_required": True,
        "coordinate_confirmation_required": True,
        "settlement_road_agriculture_infrastructure_review_required": True,
        "publication_remains_prohibited": True,
    },
    640: {
        "review_routing_action": "ACCEPT_FOR_FIELD_VERIFICATION",
        "acceptance_condition": "CONDITIONAL_DAM_VERIFICATION",
        "dam_safety_verification_required": True,
        "operational_authority_verification_required": True,
        "visitor_accessibility_verification_required": True,
        "institutional_presentation_authority_required": True,
        "publication_remains_prohibited": True,
    },
    770: {
        "review_routing_action": "RETURN_FOR_DESCRIPTION",
        "scope_review_required": True,
        "reason": "DESCRIPTION_CONTAINS_NON_NATURAL_OR_MIXED_SCOPE_SIGNALS",
        "natural_spring_identity_confirmation_required": True,
        "field_acceptance_blocked_until_description_and_scope_resolved": True,
        "publication_remains_prohibited": True,
    },
    817: {
        "review_routing_action": "ACCEPT_FOR_FIELD_VERIFICATION",
        "field_verification_required": True,
        "identity_confirmation_required": True,
        "coordinate_confirmation_required": True,
        "publication_remains_prohibited": True,
    },
    849: {
        "review_routing_action": "ACCEPT_FOR_FIELD_VERIFICATION",
        "island_identity_confirmation_required": True,
        "coordinate_confirmation_required": True,
        "access_verification_required": True,
        "environmental_sensitivity_review_required": True,
        "publication_remains_prohibited": True,
    },
    938: {
        "review_routing_action": "RETURN_FOR_DESCRIPTION",
        "scope_review_required": True,
        "reason": "DESCRIPTION_CONTAINS_NON_NATURAL_OR_MIXED_SCOPE_SIGNALS",
        "island_identity_confirmation_required": True,
        "field_acceptance_blocked_until_description_and_scope_resolved": True,
        "publication_remains_prohibited": True,
    },
}
ALLOWED_CHANGED = {
    "backend/data/gis/high-priority-natural-candidates.institutional-review.json",
    "backend/scripts/high_priority_natural_candidates.py",
    "backend/tests/unit/scripts/test_high_priority_natural_candidates.py",
    "backend/docs/high-priority-natural-candidates.md",
}
PROTECTED_PATHS = (
    "assets", "backend/app", "backend/models", "backend/migrations",
    "backend/data/destinations/national-destination-registry.review.json",
    "backend/data/gis/source-manifest.json", "backend/data/gis/institutional-sources.json",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
    "backend/data/governance",
)


class HighPriorityReviewError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def committed_input_bytes(root: Path = ROOT) -> bytes:
    raw = subprocess.check_output(["git", "cat-file", "blob", f"HEAD:{INPUT_RELATIVE}"], cwd=root)
    if sha256(raw) != INPUT_SHA256:
        raise HighPriorityReviewError("committed governed input SHA-256 mismatch")
    return raw


def high_candidates(source: dict) -> dict[int, dict]:
    found = {}
    for queue in source.get("candidate_queues", {}).values():
        for record in queue:
            if record.get("editorial_priority_band") == "HIGH_EDITORIAL_PRIORITY":
                ordinal = record.get("source_ordinal")
                if ordinal in found:
                    raise HighPriorityReviewError(f"duplicate high-priority ordinal: {ordinal}")
                found[ordinal] = record
    if set(found) != set(EXPECTED_ACTIONS):
        raise HighPriorityReviewError("exact seven high-priority source ordinals changed")
    return found


def _check(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _validate_candidate(candidate: dict, governed: dict, errors: list[str]) -> None:
    identity = candidate.get("identity", {})
    evidence = candidate.get("source_evidence", {})
    readiness = candidate.get("editorial_readiness", {})
    review = candidate.get("institutional_review", {})
    ordinal = identity.get("source_ordinal")
    _check(ordinal in EXPECTED_ACTIONS, errors, f"unexpected candidate ordinal {ordinal}")
    if ordinal not in EXPECTED_ACTIONS:
        return
    source = governed[ordinal]
    source_evidence = source.get("source_evidence", {})
    expected_identity = {
        "editorial_candidate_id": source.get("editorial_review_id"),
        "governed_review_id": source.get("governed_review_id"),
        "source_ordinal": ordinal,
        "raw_name_ar": source.get("raw_name"),
        "proposed_normalized_name_ar": source.get("normalized_name"),
        "sourced_name_en": None,
        "priority_category": source.get("priority_category"),
        "geometry_type": source_evidence.get("geometry", {}).get("type"),
        "coordinates": source_evidence.get("geometry", {}).get("coordinates"),
        "sourced_region_ar": None,
        "sourced_locality_ar": None,
    }
    _check(identity == expected_identity, errors, f"identity or coordinate evidence drift {ordinal}")
    _check(evidence.get("complete_source_description") == source_evidence.get("raw_description"), errors, f"description drift {ordinal}")
    _check(evidence.get("source") == source_evidence.get("raw_source") and evidence.get("origin") == source_evidence.get("raw_origin"), errors, f"source provenance drift {ordinal}")
    _check(evidence.get("source_status") == source_evidence.get("raw_status") and evidence.get("source_type") == source_evidence.get("raw_source_type"), errors, f"source status/type drift {ordinal}")
    _check(evidence.get("folders") == source_evidence.get("raw_folders") and evidence.get("primary_category") == source_evidence.get("raw_primary_category") and evidence.get("all_categories") == source_evidence.get("raw_all_categories"), errors, f"source category drift {ordinal}")
    _check(evidence.get("preserved_properties") == source_evidence.get("preserved_properties"), errors, f"preserved properties drift {ordinal}")
    _check(evidence.get("overlap_state") == source.get("overlap_state") and evidence.get("existing_governed_overlaps") == source_evidence.get("existing_governed_overlaps"), errors, f"overlap evidence drift {ordinal}")
    _check(evidence.get("quality_flags") == source_evidence.get("quality_flags"), errors, f"quality flags drift {ordinal}")
    provenance = evidence.get("provenance_evidence", {})
    _check(provenance.get("governed_input_path") == INPUT_RELATIVE and provenance.get("governed_input_sha256") == INPUT_SHA256, errors, f"governed provenance drift {ordinal}")
    _check(provenance.get("governed_review_collection") == source_evidence.get("governed_review_collection") and provenance.get("governed_resolution_bucket") == source_evidence.get("governed_resolution_bucket"), errors, f"governed routing provenance drift {ordinal}")
    score = source.get("editorial_readiness_score", {})
    expected_components = {key: value for key, value in score.items() if key != "total"}
    _check(readiness.get("score") == score.get("total") and readiness.get("score_components") == expected_components, errors, f"score drift {ordinal}")
    _check(readiness.get("priority_band") == "HIGH_EDITORIAL_PRIORITY", errors, f"priority drift {ordinal}")
    _check(readiness.get("identity_quality") == source.get("identity_quality") and readiness.get("coordinate_quality") == source.get("coordinate_quality"), errors, f"identity/coordinate quality drift {ordinal}")
    _check(readiness.get("duplicate_conflict_state") == source.get("duplicate_conflict_state"), errors, f"conflict evidence drift {ordinal}")
    _check(readiness.get("media_availability") == source.get("media_availability") and readiness.get("media_rights_status") == source.get("media_rights_status"), errors, f"media evidence drift {ordinal}")
    _check(review.get("review_routing_action") == EXPECTED_ACTIONS[ordinal], errors, f"review action drift {ordinal}")
    _check(review.get("routing_requirements") == ROUTING_REQUIREMENTS[ordinal], errors, f"candidate safeguards drift {ordinal}")
    _check(review.get("institutional_decision") == "PENDING" and review.get("review_routing_is_final_approval") is False and review.get("recommended_action_is_approval") is False, errors, f"routing became approval {ordinal}")
    _check(candidate.get("governance") == GOVERNANCE, errors, f"candidate governance drift {ordinal}")
    coordinates = identity.get("coordinates")
    _check(isinstance(coordinates, list) and len(coordinates) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in coordinates), errors, f"invalid coordinates {ordinal}")


def validate_artifact(artifact: dict, root: Path = ROOT, check_git: bool = True) -> dict:
    errors: list[str] = []
    try:
        source = json.loads(committed_input_bytes(root))
        governed = high_candidates(source)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, HighPriorityReviewError) as exc:
        raise HighPriorityReviewError(str(exc)) from exc
    _check(artifact.get("schema_version") == "1.0.0", errors, "schema version mismatch")
    _check(artifact.get("status") == "REVIEW_ONLY_NOT_PUBLICATION_APPROVAL", errors, "review status mismatch")
    _check(artifact.get("purpose") == "EXTERNAL_INSTITUTIONAL_REVIEW_PREPARATION", errors, "purpose mismatch")
    provenance = artifact.get("source_provenance", {})
    _check(provenance.get("governed_input_path") == INPUT_RELATIVE and provenance.get("governed_input_sha256") == INPUT_SHA256, errors, "packet provenance mismatch")
    _check(provenance.get("selection_rule") == "EDITORIAL_PRIORITY_BAND_EQUALS_HIGH_EDITORIAL_PRIORITY", errors, "selection rule mismatch")
    candidates = artifact.get("candidates", [])
    ordinals = [item.get("identity", {}).get("source_ordinal") for item in candidates]
    _check(tuple(ordinals) == EXPECTED_ORDINAL_ORDER, errors, "candidate ordering or ordinal membership mismatch")
    _check(len(candidates) == artifact.get("record_count") == 7, errors, "record count mismatch")
    _check(len({item.get("identity", {}).get("editorial_candidate_id") for item in candidates}) == 7, errors, "editorial IDs are not unique")
    _check(Counter(item.get("identity", {}).get("priority_category") for item in candidates) == Counter(EXPECTED_CATEGORIES), errors, "category distribution mismatch")
    _check(artifact.get("category_distribution") == EXPECTED_CATEGORIES, errors, "category summary mismatch")
    actions = Counter(item.get("institutional_review", {}).get("review_routing_action") for item in candidates)
    _check(actions == Counter(EXPECTED_DECISIONS), errors, "3/2/2 decision distribution mismatch")
    _check(artifact.get("summary", {}).get("review_routing_action_counts") == EXPECTED_DECISIONS, errors, "decision summary mismatch")
    for candidate in candidates:
        _validate_candidate(candidate, governed, errors)
    description_returns = {item["identity"]["source_ordinal"] for item in candidates if item["institutional_review"]["review_routing_action"] == "RETURN_FOR_DESCRIPTION"}
    _check(description_returns == {770, 938}, errors, "description/scope return membership mismatch")
    for candidate in candidates:
        ordinal = candidate["identity"]["source_ordinal"]
        if ordinal in description_returns:
            flags = candidate["source_evidence"].get("quality_flags", [])
            routing = candidate["institutional_review"]["routing_requirements"]
            _check("DESCRIPTION_CONTAINS_NON_NATURAL_OR_MIXED_SCOPE_SIGNALS" in flags, errors, f"mixed-scope flag missing {ordinal}")
            _check(routing.get("scope_review_required") is True and routing.get("field_acceptance_blocked_until_description_and_scope_resolved") is True, errors, f"field acceptance not blocked {ordinal}")
    summary = artifact.get("summary", {})
    _check((summary.get("publication_approval_granted"), summary.get("canonical_approval_granted"), summary.get("public_visibility_granted"), summary.get("publication_media_eligibility_granted")) == (False, False, False, False), errors, "packet grants approval, visibility, or media eligibility")
    _check(summary.get("institutional_decisions_pending") == 7 and summary.get("repository_media_available") == 0 and summary.get("media_rights_cleared") == 0, errors, "pending/media summary mismatch")
    _check(artifact.get("packet_governance") == GOVERNANCE, errors, "packet governance drift")
    try:
        green = json.loads((root / "backend/data/gis/green-mountain-tourism-curated.review.json").read_text(encoding="utf-8"))
        sahara = json.loads((root / "backend/data/gis/libyan-sahara-tourism-curated.review.json").read_text(encoding="utf-8"))
        registry = json.loads((root / "backend/data/destinations/national-destination-registry.review.json").read_text(encoding="utf-8"))
        _check(len(green["records"]) == 180 and len(sahara["records"]) == 69, errors, "curated natural counts changed")
        _check(sum(item.get("gis_record_count", 0) for item in registry["records"]) == 214, errors, "national publication GIS count changed")
        _check((root / "backend/data/governance/publication-approval-ledger.jsonl").stat().st_size == 0, errors, "approval ledger is not empty")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"protected invariant read failed: {exc}")
    if check_git:
        status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        changed = {line[3:].replace("\\", "/") for line in status.stdout.splitlines() if len(line) >= 4}
        _check(changed <= ALLOWED_CHANGED, errors, f"changed-file allowlist violation: {sorted(changed - ALLOWED_CHANGED)}")
        protected = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", *PROTECTED_PATHS], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
        _check(not protected.stdout.strip(), errors, f"protected paths changed: {protected.stdout.strip()}")
    if errors:
        raise HighPriorityReviewError("\n".join(errors))
    return {"records": 7, "decisions": EXPECTED_DECISIONS, "approved": 0, "publicly_visible": 0, "publication_media_eligible": 0}


def validate_serialization(path: Path = ARTIFACT_PATH) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise HighPriorityReviewError("artifact must be UTF-8 without BOM, LF, and exactly one final newline")
    if re.search(rb"(?i)[a-z]:[\\/]", raw) or b"visitlibya-local-backups" in raw:
        raise HighPriorityReviewError("artifact contains an absolute or external-local path")


def build_artifact(external_directory: Path, root: Path = ROOT) -> dict:
    for basename, expected in EXTERNAL_HASHES.items():
        path = external_directory / basename
        if not path.is_file() or sha256(path.read_bytes()) != expected:
            raise HighPriorityReviewError(f"corrected external packet hash mismatch: {basename}")
    artifact = json.loads((external_directory / "high-priority-natural-candidates.review.json").read_text(encoding="utf-8"))
    validate_artifact(artifact, root=root, check_git=False)
    return artifact


def main() -> int:
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "build":
            artifact = build_artifact(Path(sys.argv[2]))
            ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        elif len(sys.argv) != 1:
            raise HighPriorityReviewError("usage: high_priority_natural_candidates.py [build EXTERNAL_PACKET_DIRECTORY]")
        validate_serialization()
        result = validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
        print("High-priority natural-candidate review validation passed: " + json.dumps(result, sort_keys=True))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, HighPriorityReviewError) as exc:
        print(f"High-priority natural-candidate review validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
