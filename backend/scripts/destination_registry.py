#!/usr/bin/env python3
"""Validate the review-only National Destination Registry."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "backend/data/destinations/national-destination-registry.review.json"
DESTINATIONS_PATH = ROOT / "backend/data/dev/destinations.json"
COORDINATES_PATH = ROOT / "backend/data/dev/destination-coordinates.reviewed.json"
LEDGER_PATH = ROOT / "backend/data/governance/publication-approval-ledger.jsonl"
NATURAL_LAYER_PATH = ROOT / "assets/js/data/natural-tourism-layers.js"

EXPECTED_KEYS = [
    "leptis-magna",
    "sabratha",
    "shahat-cyrene",
    "tripoli",
    "benghazi",
    "green-mountain",
    "acacus",
    "natural-desert-lakes",
    "ghadames",
    "waddan",
    "hun",
    "sokna",
    "nafusa-mountains",
    "awjila",
    "girza",
]
PRIORITY_TIERS = {"PRIMARY", "COMPLEMENTARY"}
ENTITY_TYPES = {
    "ARCHAEOLOGICAL_HERITAGE_SITE",
    "GEOGRAPHIC_CITY",
    "GEOGRAPHIC_REGION",
    "NATURAL_DESTINATION",
    "COMPOSITE_CULTURAL_NATURAL_DESTINATION",
    "THEMATIC_NESTED_COLLECTION",
}
REPRESENTATION_MODES = {
    "INDEPENDENT_CANONICAL_DESTINATION",
    "REPRESENTED_THROUGH_PARENT_DESTINATION",
    "NESTED_COLLECTION_WITHIN_PARENT",
    "REPOSITORY_MENTION_ONLY",
    "NOT_FOUND_IN_REPOSITORY",
}
COORDINATE_STATUSES = {
    "REVIEWED_AUTHORITATIVE_PAIR",
    "REVIEW_REQUIRED",
    "REVIEW_REQUIRED_AGGREGATE",
    "IDENTITY_REVIEW_REQUIRED",
    "NOT_APPLICABLE_COLLECTION",
}
IDENTITY_STATUSES = {
    "REPOSITORY_IDENTITY_CONFIRMED",
    "INSTITUTIONAL_IDENTITY_REVIEW_REQUIRED",
    "PARENT_RELATIONSHIP_CONFIRMED_BY_REPOSITORY",
    "PROJECT_IDENTITY_MODEL_RESOLVED",
}
IDENTITY_MODEL_STATUSES = {"PROJECT_MODEL_RESOLVED", "REPOSITORY_EVIDENCE_ONLY", "INSTITUTIONAL_REVIEW_REQUIRED"}
PROJECT_IDENTITY_DECISIONS = {
    "UNIFIED_CYRENE_SHAHAT_DESTINATION",
    "BROADER_GHADAMES_DESTINATION_WITH_HERITAGE_CORE",
    "COMPOSITE_CULTURAL_NATURAL_DESTINATION",
}
RUNTIME_PROMOTION_STATUSES = {"NOT_PROMOTED", "REVIEW_REQUIRED"}
IDENTITY_RELATIONSHIPS = {"WITHIN_REGION", "CONTAINS_HERITAGE_CORE"}
DESTINATION_DIMENSIONS = {
    "ARCHAEOLOGICAL_HERITAGE",
    "CITY_SERVICE_CONTEXT",
    "MODERN_CITY",
    "HISTORIC_HERITAGE_CORE",
    "OASIS",
    "DESERT_AND_CULTURAL_LANDSCAPE",
    "ARCHAEOLOGY",
    "ROCK_ART_AND_INSCRIPTIONS",
    "CULTURAL_HERITAGE",
    "NATURE_AND_DESERT_LANDSCAPE",
    "GEOLOGY_AND_GEOMORPHOLOGY",
}
PROMOTIONAL_VERIFICATION_STATUSES = {"SOURCE_VERIFICATION_REQUIRED", "VERIFIED_IN_REPOSITORY"}
COVERAGE_STATUSES = {
    "FULL_GOVERNED_GIS_COVERAGE",
    "PUBLIC_DESTINATION_WITHOUT_DETAILED_GIS",
    "NESTED_GIS_COLLECTION",
    "HERITAGE_IDENTITY_REVIEW_REQUIRED",
    "PARTIAL_REPOSITORY_COVERAGE",
    "NOT_FOUND",
}
ELIGIBILITY_CLASSES = {
    "LEGACY_PUBLIC_BASELINE_NOT_INSTITUTIONAL_APPROVAL",
    "GOVERNED_RECORD_INELIGIBLE",
}
REQUIRED_RECORD_FIELDS: dict[str, type | tuple[type, ...]] = {
    "registry_record_id": str,
    "coverage_unit_key": str,
    "development_priority_tier": str,
    "name_ar": str,
    "name_en": str,
    "current_canonical_slug": (str, type(None)),
    "alternate_repository_names": list,
    "entity_type": str,
    "representation_mode": str,
    "parent_destination_slug": (str, type(None)),
    "public_destination_record_present": bool,
    "details_route_present": bool,
    "arabic_route_supported": bool,
    "english_route_supported": bool,
    "coordinates_present": bool,
    "coordinate_source": (str, type(None)),
    "coordinate_validation_status": str,
    "media_present": bool,
    "responsive_media_present": bool,
    "gis_layer_present": bool,
    "gis_layer_ids": list,
    "gis_record_count": int,
    "gis_record_selector": (dict, type(None)),
    "governed_provenance_present": bool,
    "heritage_review_present": bool,
    "legacy_public_visibility": bool,
    "institutional_publication_approved": bool,
    "publication_eligibility_classification": str,
    "identity_review_status": str,
    "coverage_status": str,
    "data_gaps": list,
    "institutional_actions_required": list,
    "evidence": list,
}


class RegistryValidationError(ValueError):
    """Raised when the review registry contradicts its repository evidence."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RegistryValidationError(f"cannot parse JSON {path}: {exc}") from exc


def _error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _repo_path(root: Path, value: str, errors: list[str], label: str) -> Path | None:
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "\\" in value:
        errors.append(f"{label} must be a relative POSIX repository path: {value!r}")
        return None
    resolved = root.joinpath(*posix.parts)
    if not resolved.is_file():
        errors.append(f"{label} does not exist: {value}")
        return None
    return resolved


def _ledger_has_approved_event(path: Path) -> bool:
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RegistryValidationError(f"invalid approval ledger JSONL line {line_number}: {exc}") from exc
        if event.get("decision") == "APPROVED" or event.get("resulting_state") == "APPROVED":
            return True
    return False


def _validate_identity_model(record: dict[str, Any], errors: list[str]) -> None:
    label = f"record {record.get('coverage_unit_key')} identity_model"
    model = record.get("identity_model")
    required = {
        "identity_model_status",
        "project_identity_decision",
        "current_repository_representation",
        "future_canonical_slug",
        "regional_relationships",
        "contained_heritage_entities",
        "destination_dimensions",
        "promotional_identity",
        "evidence_completion_required",
        "runtime_promotion_status",
    }
    if not isinstance(model, dict) or set(model) != required:
        errors.append(f"{label} must contain the deterministic identity-model fields")
        return
    _error(errors, model["identity_model_status"] in IDENTITY_MODEL_STATUSES, f"{label} has unsupported status")
    _error(errors, model["project_identity_decision"] in PROJECT_IDENTITY_DECISIONS, f"{label} has unsupported project decision")
    _error(errors, model["runtime_promotion_status"] in RUNTIME_PROMOTION_STATUSES, f"{label} has unsupported runtime promotion status")
    _error(errors, isinstance(model["future_canonical_slug"], (str, type(None))), f"{label} future slug has invalid type")
    current = model["current_repository_representation"]
    _error(
        errors,
        isinstance(current, dict)
        and set(current) == {"canonical_slug", "routed_via_slug", "dedicated_public_route_present"}
        and isinstance(current.get("dedicated_public_route_present"), bool),
        f"{label} current repository representation is invalid",
    )
    for field in ("regional_relationships", "contained_heritage_entities"):
        _error(errors, isinstance(model[field], list), f"{label} {field} must be an array")
        if isinstance(model[field], list):
            for relationship in model[field]:
                _error(errors, isinstance(relationship, dict) and relationship.get("relationship") in IDENTITY_RELATIONSHIPS, f"{label} contains an unsupported relationship")
    dimensions = model["destination_dimensions"]
    _error(errors, isinstance(dimensions, list) and all(item in DESTINATION_DIMENSIONS for item in dimensions), f"{label} contains an unknown destination dimension")
    if isinstance(dimensions, list):
        _error(errors, len(dimensions) == len(set(dimensions)), f"{label} destination dimensions must be unique")
    _error(errors, isinstance(model["evidence_completion_required"], list) and all(isinstance(item, str) for item in model["evidence_completion_required"]), f"{label} evidence requirements must be strings")
    promotional = model["promotional_identity"]
    if promotional is not None:
        _error(
            errors,
            isinstance(promotional, dict)
            and set(promotional) == {"name_ar", "name_en", "verification_status", "official_title", "grants_publication_approval"}
            and promotional.get("verification_status") in PROMOTIONAL_VERIFICATION_STATUSES
            and isinstance(promotional.get("official_title"), bool)
            and isinstance(promotional.get("grants_publication_approval"), bool),
            f"{label} promotional identity is invalid",
        )


def validate_registry(root: Path = ROOT, registry_path: Path | None = None) -> dict[str, Any]:
    """Validate a registry against authoritative repository sources without writes."""
    root = root.resolve()
    registry_path = registry_path or root / REGISTRY_PATH.relative_to(ROOT)
    registry = _load_json(registry_path)
    errors: list[str] = []

    _error(errors, isinstance(registry, dict), "registry top level must be an object")
    if not isinstance(registry, dict):
        raise RegistryValidationError("\n".join(errors))
    _error(errors, registry.get("schema_version") == 1, "unsupported schema_version")
    _error(errors, registry.get("registry_id") == "visit-libya-national-destination-registry-review", "unexpected registry_id")
    scope = registry.get("scope")
    policy = registry.get("policy")
    _error(errors, isinstance(scope, dict) and scope.get("status") == "REVIEW_ONLY_NOT_RUNTIME_PUBLICATION_SOURCE", "registry must remain review-only")
    _error(errors, isinstance(policy, dict) and policy.get("read_only") is True, "registry policy must be read-only")
    _error(errors, isinstance(policy, dict) and policy.get("changes_public_visibility") is False, "registry must not change public visibility")
    _error(errors, isinstance(policy, dict) and policy.get("grants_institutional_approval") is False, "registry must not grant approval")
    _error(errors, isinstance(policy, dict) and policy.get("development_priority_grants_approval") is False, "development priority must not grant approval")
    _error(errors, isinstance(policy, dict) and policy.get("development_priority_grants_runtime_eligibility") is False, "development priority must not grant runtime eligibility")
    _error(errors, isinstance(policy, dict) and policy.get("identity_model_resolution_grants_approval") is False, "identity-model resolution must not grant approval")
    _error(errors, isinstance(policy, dict) and policy.get("identity_model_resolution_grants_runtime_eligibility") is False, "identity-model resolution must not grant runtime eligibility")
    _error(
        errors,
        registry.get("summary") == {
            "independent_canonical_destinations": 9,
            "represented_through_parent_destinations": 2,
            "repository_evidence_without_canonical_destination": 3,
            "not_found_in_repository": 1,
            "primary_development_priority_records": 9,
            "complementary_development_priority_records": 6,
            "records_with_detailed_gis_coverage": 2,
            "records_with_institutional_publication_approval": 0,
            "identity_reviews_required": 1,
        },
        "registry summary does not match the initial review scope",
    )

    source_inventory = registry.get("source_inventory")
    _error(errors, isinstance(source_inventory, list) and all(isinstance(item, str) for item in source_inventory), "source_inventory must contain strings")
    if isinstance(source_inventory, list):
        _error(errors, source_inventory == sorted(source_inventory), "source_inventory must use stable lexical ordering")
        for source in source_inventory:
            if isinstance(source, str):
                _repo_path(root, source, errors, "source_inventory path")

    destinations_doc = _load_json(root / "backend/data/dev/destinations.json")
    destination_records = destinations_doc.get("records", []) if isinstance(destinations_doc, dict) else []
    destination_by_slug = {item.get("slug"): item for item in destination_records if isinstance(item, dict)}
    coordinates_doc = _load_json(root / "backend/data/dev/destination-coordinates.reviewed.json")
    coordinates_by_slug = {item.get("slug"): item for item in coordinates_doc.get("records", []) if isinstance(item, dict)}
    ledger = root / "backend/data/governance/publication-approval-ledger.jsonl"
    approved_event_exists = _ledger_has_approved_event(ledger)

    records = registry.get("records")
    _error(errors, isinstance(records, list), "records must be an array")
    if not isinstance(records, list):
        raise RegistryValidationError("\n".join(errors))
    _error(errors, len(records) == 15, "registry must contain exactly fifteen coverage records")
    keys = [record.get("coverage_unit_key") for record in records if isinstance(record, dict)]
    ids = [record.get("registry_record_id") for record in records if isinstance(record, dict)]
    _error(errors, keys == EXPECTED_KEYS, "records must follow the deterministic initial coverage order")
    _error(errors, len(keys) == len(set(keys)), "coverage_unit_key values must be unique")
    _error(errors, len(ids) == len(set(ids)), "registry_record_id values must be unique")
    priorities = [record.get("development_priority_tier") for record in records if isinstance(record, dict)]
    _error(errors, priorities.count("PRIMARY") == 9, "registry must contain exactly nine PRIMARY records")
    _error(errors, priorities.count("COMPLEMENTARY") == 6, "registry must contain exactly six COMPLEMENTARY records")

    known_gis_layers: dict[str, tuple[Path, dict[str, Any]]] = {}
    for relative in (
        "backend/data/gis/green-mountain-tourism-curated.review.json",
        "backend/data/gis/libyan-sahara-tourism-curated.review.json",
    ):
        source_path = root / relative
        source_doc = _load_json(source_path)
        known_gis_layers[source_doc.get("layer_id")] = (source_path, source_doc)

    for index, record in enumerate(records):
        label = f"record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        key = record.get("coverage_unit_key", "<unknown>")
        label = f"record {key}"
        for field, expected_type in REQUIRED_RECORD_FIELDS.items():
            if field not in record:
                errors.append(f"{label} missing required field {field}")
            elif not isinstance(record[field], expected_type):
                errors.append(f"{label} field {field} has invalid type")
        if any(field not in record for field in REQUIRED_RECORD_FIELDS):
            continue
        _error(errors, record["entity_type"] in ENTITY_TYPES, f"{label} uses unsupported entity_type")
        _error(errors, record["development_priority_tier"] in PRIORITY_TIERS, f"{label} uses unsupported development priority tier")
        _error(errors, record["representation_mode"] in REPRESENTATION_MODES, f"{label} uses unsupported representation_mode")
        _error(errors, record["coordinate_validation_status"] in COORDINATE_STATUSES, f"{label} uses unsupported coordinate status")
        _error(errors, record["identity_review_status"] in IDENTITY_STATUSES, f"{label} uses unsupported identity status")
        _error(errors, record["coverage_status"] in COVERAGE_STATUSES, f"{label} uses unsupported coverage status")
        _error(errors, record["publication_eligibility_classification"] in ELIGIBILITY_CLASSES, f"{label} conflicts with publication governance terminology")
        if key in {"shahat-cyrene", "ghadames", "acacus"}:
            _validate_identity_model(record, errors)
        _error(errors, all(isinstance(item, str) for item in record["alternate_repository_names"]), f"{label} alternate names must be strings")
        _error(errors, all(isinstance(item, str) for item in record["data_gaps"]), f"{label} data gaps must be strings")
        _error(errors, all(isinstance(item, str) for item in record["institutional_actions_required"]), f"{label} actions must be strings")

        slug = record["current_canonical_slug"]
        parent = record["parent_destination_slug"]
        if slug is not None:
            _error(errors, slug in destination_by_slug, f"{label} claims unknown canonical slug {slug!r}")
        if parent is not None:
            _error(errors, parent in destination_by_slug, f"{label} claims unknown parent slug {parent!r}")
        if record["public_destination_record_present"]:
            _error(errors, slug in destination_by_slug, f"{label} claims a public record without a canonical slug")

        if record["coordinates_present"]:
            coordinate = coordinates_by_slug.get(slug)
            _error(errors, coordinate is not None, f"{label} has no reviewed authoritative coordinate")
            if coordinate:
                latitude, longitude = coordinate.get("latitude"), coordinate.get("longitude")
                valid = (
                    isinstance(latitude, (int, float)) and not isinstance(latitude, bool)
                    and isinstance(longitude, (int, float)) and not isinstance(longitude, bool)
                    and math.isfinite(latitude) and math.isfinite(longitude)
                    and -90 <= latitude <= 90 and -180 <= longitude <= 180
                )
                _error(errors, valid, f"{label} authoritative coordinate pair is invalid")
            _error(errors, record["coordinate_source"] == "backend/data/dev/destination-coordinates.reviewed.json", f"{label} coordinate source is not authoritative")
        else:
            _error(errors, record["coordinate_source"] is None, f"{label} must not claim a coordinate source")

        layer_ids = record["gis_layer_ids"]
        _error(errors, all(isinstance(item, str) for item in layer_ids), f"{label} GIS layer IDs must be strings")
        _error(errors, record["gis_layer_present"] == bool(layer_ids), f"{label} GIS presence conflicts with layer IDs")
        if not layer_ids:
            _error(errors, record["gis_record_count"] == 0 and record["gis_record_selector"] is None, f"{label} must not claim GIS records")
        else:
            _error(errors, len(layer_ids) == 1, f"{label} must identify one authoritative GIS layer")
            layer_id = layer_ids[0]
            _error(errors, layer_id in known_gis_layers, f"{label} claims unknown GIS layer {layer_id!r}")
            selector = record["gis_record_selector"]
            if layer_id in known_gis_layers and isinstance(selector, dict):
                source_path, source_doc = known_gis_layers[layer_id]
                expected_source = source_path.relative_to(root).as_posix()
                _error(errors, selector.get("source_path") == expected_source, f"{label} GIS selector source mismatch")
                source_records = source_doc.get("records", [])
                if selector.get("mode") == "ALL_RECORDS":
                    selected = source_records
                elif selector.get("mode") == "PRIMARY_CATEGORY" and isinstance(selector.get("primary_category"), str):
                    selected = [item for item in source_records if item.get("primary_category") == selector["primary_category"]]
                else:
                    selected = []
                    errors.append(f"{label} has unsupported GIS record selector")
                _error(errors, record["gis_record_count"] == len(selected), f"{label} GIS record count does not match authoritative source")
            else:
                _error(errors, isinstance(selector, dict), f"{label} requires a GIS record selector")

        for evidence_index, evidence in enumerate(record["evidence"]):
            evidence_label = f"{label} evidence[{evidence_index}]"
            if not isinstance(evidence, dict) or set(evidence) != {"path", "identifiers"}:
                errors.append(f"{evidence_label} must contain path and identifiers")
                continue
            if not isinstance(evidence["path"], str):
                errors.append(f"{evidence_label} path must be a string")
            else:
                _repo_path(root, evidence["path"], errors, evidence_label)
            _error(errors, isinstance(evidence["identifiers"], list) and all(isinstance(item, str) for item in evidence["identifiers"]), f"{evidence_label} identifiers must be strings")

        if record["legacy_public_visibility"]:
            _error(errors, not record["institutional_publication_approved"], f"{label} treats legacy visibility as institutional approval")
        _error(errors, not record["institutional_publication_approved"], f"{label} development priority must not grant institutional approval")
        if not approved_event_exists:
            _error(errors, not record["institutional_publication_approved"], f"{label} claims approval while committed ledger has no approval event")

    by_key = {record.get("coverage_unit_key"): record for record in records if isinstance(record, dict)}
    lakes = by_key.get("natural-desert-lakes", {})
    _error(errors, lakes.get("current_canonical_slug") is None, "natural/desert lakes must not be promoted to an independent canonical destination")
    _error(errors, lakes.get("representation_mode") == "NESTED_COLLECTION_WITHIN_PARENT" and lakes.get("parent_destination_slug") == "desert", "natural/desert lakes must remain nested under desert")
    shahat = by_key.get("shahat-cyrene", {})
    shahat_model = shahat.get("identity_model", {})
    _error(errors, shahat.get("name_ar") == "قورينا – شحات", "Cyrene/Shahat Arabic project identity must be exact")
    _error(errors, shahat.get("name_en") == "Cyrene (Shahat)", "Cyrene/Shahat English project identity must be exact")
    _error(errors, shahat.get("current_canonical_slug") is None and "cyrene" not in destination_by_slug, "Cyrene must not claim a current runtime canonical slug")
    _error(errors, shahat_model.get("identity_model_status") == "PROJECT_MODEL_RESOLVED", "Cyrene/Shahat project identity model must be resolved")
    _error(errors, shahat_model.get("project_identity_decision") == "UNIFIED_CYRENE_SHAHAT_DESTINATION", "Cyrene/Shahat must be one unified project destination")
    _error(errors, shahat_model.get("future_canonical_slug") == "cyrene", "Cyrene future canonical slug must be cyrene")
    _error(errors, shahat_model.get("regional_relationships") == [{"relationship": "WITHIN_REGION", "destination_slug": "green-mountain"}], "Cyrene must remain within the Green Mountain region")
    _error(errors, shahat_model.get("runtime_promotion_status") == "NOT_PROMOTED" and shahat_model.get("current_repository_representation", {}).get("dedicated_public_route_present") is False, "Cyrene runtime promotion must remain disabled")
    _error(errors, not shahat.get("coordinates_present") and not shahat.get("gis_layer_present"), "Cyrene must not borrow coordinates or claim an identity-specific GIS layer")
    _error(errors, lakes.get("development_priority_tier") == "PRIMARY", "natural/desert lakes must remain PRIMARY development priority")
    _error(errors, by_key.get("ghadames", {}).get("current_canonical_slug") == "ghadames" and by_key.get("ghadames", {}).get("development_priority_tier") == "PRIMARY", "Ghadames must preserve its canonical record and PRIMARY priority")
    ghadames = by_key.get("ghadames", {})
    ghadames_model = ghadames.get("identity_model", {})
    _error(
        errors,
        ghadames.get("related_canonical_destination_relationships") == [
            {"slug": "old-city-ghadames", "relationship": "CONTAINS_HERITAGE_CORE"}
        ],
        "Ghadames must contain old-city-ghadames as its heritage core",
    )
    _error(errors, {"ghadames", "old-city-ghadames"}.issubset(destination_by_slug), "Ghadames and Old City must remain distinct authoritative canonical identities")
    _error(errors, ghadames_model.get("project_identity_decision") == "BROADER_GHADAMES_DESTINATION_WITH_HERITAGE_CORE", "Ghadames broader-destination model is invalid")
    _error(errors, ghadames_model.get("contained_heritage_entities") == [{"relationship": "CONTAINS_HERITAGE_CORE", "canonical_slug": "old-city-ghadames", "coordinate_inherited_by_destination": False, "separate_evidence_and_publication_requirements": True}], "Ghadames heritage-core containment contract is invalid")
    _error(errors, not ghadames.get("coordinates_present") and ghadames.get("coordinate_source") is None, "Old City coordinates must not be reused for broader Ghadames")

    acacus = by_key.get("acacus", {})
    acacus_model = acacus.get("identity_model", {})
    required_acacus_dimensions = ["ARCHAEOLOGY", "ROCK_ART_AND_INSCRIPTIONS", "CULTURAL_HERITAGE", "NATURE_AND_DESERT_LANDSCAPE", "GEOLOGY_AND_GEOMORPHOLOGY"]
    _error(errors, acacus.get("current_canonical_slug") == "acacus", "Acacus canonical slug must remain acacus")
    _error(errors, acacus.get("entity_type") == "COMPOSITE_CULTURAL_NATURAL_DESTINATION" and acacus_model.get("project_identity_decision") == "COMPOSITE_CULTURAL_NATURAL_DESTINATION", "Acacus must use the composite cultural-natural model")
    _error(errors, acacus_model.get("destination_dimensions") == required_acacus_dimensions, "Acacus must contain all five controlled destination dimensions in deterministic order")
    promotion = acacus_model.get("promotional_identity", {})
    _error(errors, promotion.get("name_ar") == "المتحف العالمي المفتوح" and promotion.get("name_en") == "Open-air world museum", "Acacus promotional identity wording must be exact")
    _error(errors, promotion.get("verification_status") == "SOURCE_VERIFICATION_REQUIRED" and promotion.get("official_title") is False and promotion.get("grants_publication_approval") is False, "Acacus promotional identity must remain non-official and source-verification-required")
    _error(errors, acacus_model.get("runtime_promotion_status") == "NOT_PROMOTED", "Acacus identity-model resolution must not promote runtime state")
    _error(errors, by_key.get("nafusa-mountains", {}).get("current_canonical_slug") == "nafusa" and by_key.get("nafusa-mountains", {}).get("development_priority_tier") == "COMPLEMENTARY", "Nafusa Mountains must preserve its canonical regional representation and COMPLEMENTARY priority")
    for unresolved_key in ("waddan", "hun", "sokna", "girza"):
        _error(errors, by_key.get(unresolved_key, {}).get("current_canonical_slug") is None, f"{unresolved_key} must not claim an unsupported canonical slug")

    claimed_slugs = [record["current_canonical_slug"] for record in records if record.get("current_canonical_slug")]
    _error(errors, len(claimed_slugs) == len(set(claimed_slugs)), "duplicate canonical identities require distinct records with explicit parent relationships")
    _error(errors, sum(record["gis_record_count"] for record in records) == 214, "registry-scoped GIS total must remain 214")

    layer_text = (root / "assets/js/data/natural-tourism-layers.js").read_text(encoding="utf-8")
    _error(errors, not any(f"sourceFeatureId: {candidate}" in layer_text or f'"source_feature_id": {candidate}' in layer_text for candidate in (832, 913)), "heritage IDs 832 and 913 must remain outside the natural layer")

    if errors:
        raise RegistryValidationError("\n".join(errors))
    return {"records": len(records), "gis_records": sum(record["gis_record_count"] for record in records), "approved_events": int(approved_event_exists)}


def main() -> int:
    try:
        result = validate_registry()
    except RegistryValidationError as exc:
        print("FAIL destination registry:", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 1
    print(f"PASS destination registry: {result['records']} review records; {result['gis_records']} scoped GIS records; no approval granted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
