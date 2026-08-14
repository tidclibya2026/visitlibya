"""Read-only validation for the governed heritage-candidate review artifact."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = Path("backend/data/gis/heritage-candidates.review.json")
CROSS_LAYER_PATH = Path("backend/data/gis/natural-layer-cross-layer-review.json")
EXPECTED_IDS = {832, 913}
ROUTING_PATHS = {
    832: "FORTIFICATION_HERITAGE_REVIEW",
    913: "ARCHAEOLOGICAL_SITE_REVIEW",
}
SOURCE_ARTIFACTS = [
    "backend/data/gis/natural-layer-cross-layer-review.json",
    "backend/data/gis/libyan-sahara-tourism-candidates.review.json",
]
POLICY = {
    "automatic_publication": False,
    "automatic_destination_membership": False,
    "automatic_canonical_identity": False,
    "automatic_coordinate_approval": False,
    "coordinate_generation": False,
    "database_write": False,
    "frontend_write": False,
    "source_records_deleted": False,
}
TOP_LEVEL_KEYS = {
    "schema_version", "artifact_status", "classification_policy",
    "source_artifacts", "policy", "summary", "records",
}
SOURCE_KEYS = {
    "source_feature_id", "name", "primary_category", "all_categories",
    "longitude", "latitude", "source", "origin", "status",
    "regional_layer", "selection_evidence", "media_companion_found",
    "review_status", "canonical_approval", "tourism_relevance",
    "recommended_action", "tourism_name_signals", "classification_reason",
    "publication_approved", "curation_status", "curation_reason", "matched_terms",
}
ROUTING_KEYS = {
    "routing_status", "recommended_review_path", "routing_evidence",
    "canonical_identity_approved", "coordinate_approved",
    "destination_membership_approved", "media_approved",
    "institutional_review", "publication_decision",
}
FORBIDDEN_EDITORIAL_KEYS = {
    "name_en", "english_name", "nameEn", "slug", "destination_slug",
    "municipality", "municipality_ar", "municipality_en", "description",
    "description_ar", "description_en", "historical_period", "period",
    "generated_coordinates", "source_registry_id", "source_id",
    "media_url", "media_rights", "usage_rights",
}
LEAKAGE_PATHS = [
    Path("backend/data/gis/green-mountain-tourism-curated.review.json"),
    Path("backend/data/gis/libyan-sahara-tourism-curated.review.json"),
    Path("assets/js/data/natural-tourism-layers.js"),
    Path("backend/data/dev/destinations.json"),
    Path("assets/js/data/curated-destinations.js"),
    Path("heritage.html"),
    Path("ar/heritage.html"),
]


class HeritageValidationError(ValueError):
    """A heritage review invariant was violated."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HeritageValidationError(f"cannot read valid UTF-8 JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HeritageValidationError(f"{path} must contain a JSON object")
    return payload


def _cross_records(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    try:
        records = payload["records"]["sahara_cross_layer"]
    except (KeyError, TypeError) as exc:
        raise HeritageValidationError("cross-layer Sahara records are missing") from exc
    selected = {
        item.get("source_feature_id"): item
        for item in records
        if isinstance(item, dict) and item.get("source_feature_id") in EXPECTED_IDS
    }
    if set(selected) != EXPECTED_IDS:
        raise HeritageValidationError("cross-layer evidence must contain exactly IDs 832 and 913")
    return selected


def _assert_exact_keys(actual: dict[str, Any], expected: set[str], label: str) -> None:
    if set(actual) != expected:
        missing = sorted(expected - set(actual))
        extra = sorted(set(actual) - expected)
        raise HeritageValidationError(f"{label} keys differ; missing={missing}, extra={extra}")


def _validate_routing_evidence(feature_id: int, evidence: Any) -> None:
    if not isinstance(evidence, dict):
        raise HeritageValidationError(f"ID {feature_id}: routing_evidence must be an object")
    _assert_exact_keys(
        evidence,
        {"observed_name_signals", "supporting_tracked_occurrences", "evidence_scope"},
        f"ID {feature_id} routing_evidence",
    )
    expected_signals = ["قلعة"] if feature_id == 832 else ["الأثري"]
    expected_occurrences = ["التراث الثقافي.docx"] if feature_id == 832 else []
    if evidence["observed_name_signals"] != expected_signals:
        raise HeritageValidationError(f"ID {feature_id}: unsupported routing name evidence")
    if evidence["supporting_tracked_occurrences"] != expected_occurrences:
        raise HeritageValidationError(f"ID {feature_id}: unsupported supporting occurrence")
    if evidence["evidence_scope"] != "ROUTING_ONLY_NOT_IDENTITY_APPROVAL":
        raise HeritageValidationError(f"ID {feature_id}: routing evidence scope is invalid")


def validate_payload(artifact: dict[str, Any], cross_layer: dict[str, Any]) -> None:
    _assert_exact_keys(artifact, TOP_LEVEL_KEYS, "artifact")
    if artifact["schema_version"] != 1:
        raise HeritageValidationError("unsupported schema_version")
    if artifact["artifact_status"] != "HUMAN_REVIEW_ONLY_NOT_PUBLICATION_APPROVAL":
        raise HeritageValidationError("artifact_status is not review-only")
    if not isinstance(artifact["classification_policy"], str) or not artifact["classification_policy"].strip():
        raise HeritageValidationError("classification_policy is required")
    if artifact["source_artifacts"] != SOURCE_ARTIFACTS:
        raise HeritageValidationError("source_artifacts do not match the governed provenance set")
    if artifact["policy"] != POLICY:
        raise HeritageValidationError("artifact policy must disable every automatic/write action")
    if artifact["summary"] != {"candidate_count": 2, "review_required": 2, "publication_approved": 0}:
        raise HeritageValidationError("artifact summary is invalid")
    records = artifact["records"]
    if not isinstance(records, list) or len(records) != 2:
        raise HeritageValidationError("artifact must contain exactly two records")
    ids = [item.get("source_feature_id") for item in records if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        raise HeritageValidationError("duplicate source_feature_id")
    if set(ids) != EXPECTED_IDS:
        raise HeritageValidationError("artifact must contain exactly IDs 832 and 913")

    sources = _cross_records(cross_layer)
    for record in records:
        feature_id = record["source_feature_id"]
        _assert_exact_keys(record, SOURCE_KEYS | ROUTING_KEYS, f"ID {feature_id}")
        if FORBIDDEN_EDITORIAL_KEYS & set(record):
            raise HeritageValidationError(f"ID {feature_id}: forbidden editorial/source-mapping field")
        source = sources[feature_id]
        for key in SOURCE_KEYS:
            if record[key] != source[key]:
                raise HeritageValidationError(f"ID {feature_id}: {key} differs from cross-layer evidence")
        latitude, longitude = record["latitude"], record["longitude"]
        if isinstance(latitude, bool) or isinstance(longitude, bool):
            raise HeritageValidationError(f"ID {feature_id}: coordinates must be numeric")
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (latitude, longitude)):
            raise HeritageValidationError(f"ID {feature_id}: coordinates must be finite")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise HeritageValidationError(f"ID {feature_id}: coordinates are outside WGS84 bounds")
        if record["routing_status"] != "HERITAGE_REVIEW_REQUIRED":
            raise HeritageValidationError(f"ID {feature_id}: invalid routing_status")
        if record["recommended_review_path"] != ROUTING_PATHS[feature_id]:
            raise HeritageValidationError(f"ID {feature_id}: invalid recommended_review_path")
        _validate_routing_evidence(feature_id, record["routing_evidence"])
        false_fields = (
            "canonical_approval", "publication_approved", "canonical_identity_approved",
            "coordinate_approved", "destination_membership_approved", "media_approved",
        )
        if any(record[field] is not False for field in false_fields):
            raise HeritageValidationError(f"ID {feature_id}: all approval fields must be false")
        if record["review_status"] != "REVIEW_REQUIRED":
            raise HeritageValidationError(f"ID {feature_id}: review_status must remain REVIEW_REQUIRED")
        if record["institutional_review"] is not None or record["publication_decision"] is not None:
            raise HeritageValidationError(f"ID {feature_id}: institutional decisions must remain null")
        if source.get("routing_status") != "ROUTED_TO_HERITAGE_CANDIDATE_REVIEW":
            raise HeritageValidationError(f"ID {feature_id}: cross-layer routing_status mismatch")
        if source.get("routed_artifact") != ARTIFACT_PATH.as_posix():
            raise HeritageValidationError(f"ID {feature_id}: cross-layer routed_artifact mismatch")
        if source.get("recommended_review_path") != ROUTING_PATHS[feature_id]:
            raise HeritageValidationError(f"ID {feature_id}: cross-layer review path mismatch")


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي"}))
    return re.sub(r"[^\w]+", "", value).casefold()


def _json_source_ids(value: Any) -> set[int]:
    found: set[int] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"source_feature_id", "sourceFeatureId"} and child in EXPECTED_IDS:
                found.add(child)
            found.update(_json_source_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_json_source_ids(child))
    return found


def validate_no_leakage(contents: dict[str, str]) -> None:
    target_names = {_normalized("قلعة ام العبيد"), _normalized("قصر أم الحمام الأثري")}
    for name, content in contents.items():
        suffix = Path(name).suffix.lower()
        leaked_ids: set[int] = set()
        if suffix == ".json":
            try:
                leaked_ids = _json_source_ids(json.loads(content))
            except json.JSONDecodeError as exc:
                raise HeritageValidationError(f"leakage target is invalid JSON: {name}") from exc
        elif suffix == ".js":
            for feature_id in EXPECTED_IDS:
                if re.search(rf"\bsourceFeatureId\s*:\s*{feature_id}\b|\"sourceFeatureId\"\s*:\s*{feature_id}\b", content):
                    leaked_ids.add(feature_id)
        normalized = _normalized(content)
        leaked_names = [item for item in target_names if item in normalized]
        if leaked_ids or leaked_names:
            raise HeritageValidationError(f"heritage candidate leaked into published/natural data: {name}")


def _validate_tracked_sources(root: Path, paths: list[str]) -> None:
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise HeritageValidationError(f"source artifact does not exist: {relative}")
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise HeritageValidationError(f"source artifact is not tracked: {relative}")


def validate_repository(root: Path = REPOSITORY_ROOT) -> None:
    artifact = _load_json(root / ARTIFACT_PATH)
    cross_layer = _load_json(root / CROSS_LAYER_PATH)
    validate_payload(artifact, cross_layer)
    _validate_tracked_sources(root, artifact["source_artifacts"])
    contents: dict[str, str] = {}
    for relative in LEAKAGE_PATHS:
        path = root / relative
        if not path.is_file():
            raise HeritageValidationError(f"required leakage target is missing: {relative.as_posix()}")
        contents[relative.as_posix()] = path.read_text(encoding="utf-8")
    validate_no_leakage(contents)


def main() -> int:
    try:
        validate_repository()
    except HeritageValidationError as exc:
        print(f"FAIL heritage candidate review: {exc}", file=sys.stderr)
        return 1
    print("PASS heritage candidate review: 2 routed records; approvals false; no natural, destination, or frontend leakage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
