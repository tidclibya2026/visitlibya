#!/usr/bin/env python3
"""Validate the review-only Leptis Magna and Sabratha GIS scope contracts."""

from __future__ import annotations

import json
import hashlib
import math
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCOPE_PATHS = (
    Path("backend/data/gis/leptis-magna-heritage-scope.review.json"),
    Path("backend/data/gis/sabratha-heritage-scope.review.json"),
)
REGISTRY_PATH = Path("backend/data/destinations/national-destination-registry.review.json")
COORDINATES_PATH = Path("backend/data/dev/destination-coordinates.reviewed.json")
CANONICAL_REVIEW_PATH = Path("backend/data/gis/canonical-destination-coordinate-review.json")
LEDGER_PATH = Path("backend/data/governance/publication-approval-ledger.jsonl")
NATURAL_LAYER_PATH = Path("assets/js/data/natural-tourism-layers.js")

EXPECTED = {
    "leptis-magna": {
        "scope_id": "heritage-scope-leptis-magna-v1",
        "registry_record_id": "ndr-leptis-magna",
        "name_ar": "لبدة الكبرى",
        "name_en": "Leptis Magna",
        "longitude": 14.2883012,
        "latitude": 32.6389502,
        "source_reference": "مواقع التراث العالمي الخمسة_LY.kml#Placemark-1",
        "source_feature_id": "fp-0ce1a2534b980be1145494f4",
    },
    "sabratha": {
        "scope_id": "heritage-scope-sabratha-v1",
        "registry_record_id": "ndr-sabratha",
        "name_ar": "صبراتة",
        "name_en": "Sabratha",
        "longitude": 12.484983,
        "latitude": 32.805035,
        "source_reference": "مواقع التراث العالمي الخمسة_LY.kml#Placemark-2",
        "source_feature_id": "fp-e602be9583f488fb120439db",
    },
}
TAXONOMY = (
    "ARCHAEOLOGICAL_MONUMENT",
    "ARCHAEOLOGICAL_STRUCTURE",
    "MOSAIC_OR_ARTIFACT_CONTEXT",
    "SITE_ENTRANCE",
    "VISITOR_CENTER",
    "MUSEUM",
    "INTERPRETATION_POINT",
    "ACCESS_ROUTE",
    "VISITOR_SERVICE",
    "PROTECTION_OR_BUFFER_ZONE",
    "DOCUMENTED_VIEWPOINT",
    "OTHER_REVIEW_REQUIRED",
)
GEOMETRY_TYPES = {"Point", "LineString", "Polygon", "MultiPolygon"}
INVENTORY_EXPECTED = {
    "leptis-magna": {
        "artifact_basename": "leptis_points_review.esri.json",
        "source_layer": "leptis_points_review",
        "sha256": "51be7a822a221e3ff4170c2f0104a83a9a99fc3b3ea916ca3a57a7723fd6f281",
        "record_count": 51,
        "fields": ["OBJECTID_12", "OBJECTID_1", "FID_1", "objectid", "name", "popupinfo", "en_name", "photo"],
    },
    "sabratha": {
        "artifact_basename": "sabratha_points_review.esri.json",
        "source_layer": "sabratha_points_review",
        "sha256": "ffb3612844670770fafedf559860827a37b2ee556ee28794c94a6d62652de5d3",
        "record_count": 39,
        "fields": ["OBJECTID_1", "OBJECTID", "ID", "اسم_ا", "X", "Y", "الوصف"],
    },
}
REVIEW_CLASSIFICATIONS = {
    "ARCHAEOLOGICAL_OR_HERITAGE_FEATURE",
    "VISITOR_SERVICE_OR_FACILITY",
    "LANDSCAPE_OR_NATURAL_CONTEXT",
    "UNRESOLVED_REVIEW_REQUIRED",
}
PROTECTED_PATHS = {
    "assets/js/data/natural-tourism-layers.js",
    "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json",
    "backend/data/governance/legacy-publication-baseline.json",
    "backend/data/governance/publication-approval-ledger.jsonl",
    "backend/data/governance/publication-generation-manifest.json",
    "backend/data/governance/publication-policy.json",
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
}


class HeritageScopeValidationError(ValueError):
    """Raised when a heritage scope contract contradicts governed evidence."""


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _classify(slug: str, name: str) -> tuple[str, str]:
    visitor = ("مركز", "موقف", "استراحة", "مقاهي", "مطعم", "منتزه", "مصيف", "متحف")
    landscape = ("وادي",)
    archaeology = (
        "بوابة", "حمامات", "قوس", "معبد", "ميدان", "المعبد", "شرفة", "نصب", "مدرسة",
        "الميناء", "ساحة", "مدخل الميناء", "منارة", "برج", "مسرح", "ضريح", "نيمافيوم",
        "جدار", "الجدار", "بالسترا", "باسيل", "السوق", "كنيسة", "كوريا", "معمودية",
        "Tombs", "شارع الآثار", "ريجيو", "نافورة", "ديوان", "المبنى", "مبنى", "منزل",
        "بيت", "مقابر", "Serapaeum",
    )
    if any(term in name for term in visitor):
        return "VISITOR_SERVICE_OR_FACILITY", "Source name explicitly identifies a visitor service or facility; classification remains review-only."
    if any(term in name for term in landscape):
        return "LANDSCAPE_OR_NATURAL_CONTEXT", "Source name explicitly identifies landscape or natural context; classification remains review-only."
    if any(term in name for term in archaeology):
        return "ARCHAEOLOGICAL_OR_HERITAGE_FEATURE", "Source name contains an archaeological or heritage feature term; classification remains review-only."
    return "UNRESOLVED_REVIEW_REQUIRED", "Source name alone does not support a controlled review classification."


def _attachment_state(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip().startswith("___json"):
        return None
    try:
        json.loads(value.strip()[7:])
    except json.JSONDecodeError:
        return "TRUNCATED_ATTACHMENT_JSON"
    return "PARSEABLE_ATTACHMENT_JSON"


def build_review_inventory(slug: str, export: dict[str, Any], artifact_basename: str, sha256: str) -> dict[str, Any]:
    """Create a deterministic, non-public point inventory from an ArcGIS JSON export."""
    expected = INVENTORY_EXPECTED[slug]
    features = export.get("features", [])
    name_field = "name" if slug == "leptis-magna" else "اسم_ا"
    names = [(item.get("attributes", {}).get(name_field) or "").strip() for item in features]
    coord_names: dict[tuple[float, float, str], int] = {}
    coordinates: dict[tuple[float, float], list[str]] = {}
    for feature, name in zip(features, names):
        geometry = feature.get("geometry", {})
        key = (geometry.get("x"), geometry.get("y"), name)
        coord_names[key] = coord_names.get(key, 0) + 1
        coordinates.setdefault((geometry.get("x"), geometry.get("y")), []).append(name)

    records: list[dict[str, Any]] = []
    for feature, name in zip(features, names):
        attributes = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        identity_payload = {
            "source_database": "points_world_heritage.gdb",
            "source_layer": expected["source_layer"],
            "source_attributes": attributes,
            "geometry": {"x": geometry.get("x"), "y": geometry.get("y"), "wkid": 4326},
        }
        digest = hashlib.sha256(json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
        classification, basis = _classify(slug, name)
        flags: list[str] = []
        coord = (geometry.get("x"), geometry.get("y"))
        if coord_names.get((coord[0], coord[1], name), 0) > 1:
            flags.append("DUPLICATE_EXACT_NAME_AND_COORDINATE_REVIEW")
        if len(set(coordinates.get(coord, []))) > 1:
            flags.append("EXACT_COORDINATE_IDENTITY_CONFLICT_REVIEW")

        proposed_name = None
        if slug == "leptis-magna":
            if attributes.get("objectid") == 0:
                flags.append("NON_UNIQUE_MUTABLE_OBJECTID_REVIEW")
            en_state = _attachment_state(attributes.get("en_name"))
            photo_state = _attachment_state(attributes.get("photo"))
            if en_state:
                flags.extend(["ATTACHMENT_JSON_IN_EN_NAME_FIELD_REVIEW", en_state])
            if photo_state:
                flags.extend(["PHOTO_ATTACHMENT_REFERENCE_REVIEW", photo_state])
            if name == "قوس سبتيموس سفيروس" and "قوس الإمبراطور تراجان" in str(attributes.get("photo", "")):
                flags.append("MEDIA_IDENTITY_CONFLICT_REVIEW")
        else:
            repeated_names = {"معبد سيرابيس", "حوض المعمودية", "معبد ايزيس وإيزوريس"}
            if name in repeated_names:
                flags.append("REPEATED_NAME_DISTINCT_COORDINATES_REVIEW")
            if name in {"معبد سيرابيس", "Serapaeum (Sabratha"}:
                flags.append("SERAPAEUM_IDENTITY_NORMALIZATION_REVIEW")
            if name == "Serapaeum (Sabratha":
                flags.append("INCOMPLETE_SOURCE_NAME_REVIEW")
                proposed_name = "Serapaeum (Sabratha)"
            if name in {"حمامات أوفانيوس", "حمامات ريجيو السابع"}:
                flags.append("NEARBY_DISTINCT_NAMES_REVIEW")

        records.append({
            "review_feature_id": f"heritage-review-{slug}-{digest}",
            "destination_slug": slug,
            "source_database": "points_world_heritage.gdb",
            "source_layer": expected["source_layer"],
            "source_artifact_basename": artifact_basename,
            "source_attributes": attributes,
            "source_geometry": {"geometry_type": "Point", "longitude": geometry.get("x"), "latitude": geometry.get("y"), "wkid": 4326},
            "source_name": attributes.get(name_field),
            "proposed_normalized_name": proposed_name,
            "review_classification": classification,
            "classification_basis": basis,
            "quality_flags": sorted(set(flags)),
            "canonical_approval": False,
            "publication_approved": False,
            "public_visibility_enabled": False,
            "institutional_review_status": "UNRESOLVED",
        })

    classification_counts = {key: sum(item["review_classification"] == key for item in records) for key in sorted(REVIEW_CLASSIFICATIONS)}
    quality = {
        "record_count": len(records),
        "unique_nonblank_name_count": len({name for name in names if name}),
        "unique_coordinate_count": len(coordinates),
    }
    if slug == "leptis-magna":
        quality.update({
            "blank_popupinfo_count": sum(_blank(item["attributes"].get("popupinfo")) for item in features),
            "blank_en_name_count": sum(_blank(item["attributes"].get("en_name")) for item in features),
            "blank_photo_count": sum(_blank(item["attributes"].get("photo")) for item in features),
            "parseable_photo_attachment_json_count": sum(_attachment_state(item["attributes"].get("photo")) == "PARSEABLE_ATTACHMENT_JSON" for item in features),
            "truncated_photo_attachment_json_count": sum(_attachment_state(item["attributes"].get("photo")) == "TRUNCATED_ATTACHMENT_JSON" for item in features),
        })
    else:
        quality.update({
            "blank_description_count": sum(_blank(item["attributes"].get("الوصف")) for item in features),
            "geometry_xy_match_within_tolerance_count": sum(
                abs(item["geometry"]["x"] - item["attributes"]["X"]) <= 1e-6
                and abs(item["geometry"]["y"] - item["attributes"]["Y"]) <= 1e-6
                for item in features
            ),
        })
    return {
        "status": "REVIEW_ONLY_POINT_INVENTORY_NOT_RUNTIME_SOURCE",
        "source_provenance": {
            "source_database": "points_world_heritage.gdb",
            "source_layer": expected["source_layer"],
            "source_artifact_basename": artifact_basename,
            "source_artifact_sha256": sha256,
            "source_record_count": len(records),
            "source_geometry_type": export.get("geometryType"),
            "source_wkid": export.get("spatialReference", {}).get("wkid"),
            "source_field_names": [field.get("name") for field in export.get("fields", [])],
            "extraction_date": "2026-08-22",
            "absolute_source_path_recorded": False,
        },
        "identity_policy": "Content-derived IDs bind source database and layer identity, all preserved source attributes, and coordinates; mutable ArcGIS OIDs are not sole identities.",
        "classification_policy": "Review-only name-evidence routing; proximity and repeated names do not deduplicate, approve, or establish canonical identity.",
        "media_policy": "Attachment references are preserved as source values only and grant no ownership, usage rights, identity, or publication authority.",
        "boundary_authority": False,
        "quality_summary": quality,
        "classification_counts": classification_counts,
        "records": records,
    }


def import_review_inventories(leptis_path: Path, sabratha_path: Path, root: Path = ROOT) -> None:
    """Import two verified exports into existing scope files with deterministic serialization."""
    for slug, source_path, scope_path in zip(EXPECTED, (leptis_path, sabratha_path), SCOPE_PATHS):
        raw = source_path.read_bytes()
        sha256 = hashlib.sha256(raw).hexdigest()
        export = json.loads(raw.decode("utf-8-sig"))
        expected = INVENTORY_EXPECTED[slug]
        if source_path.name != expected["artifact_basename"] or sha256 != expected["sha256"]:
            raise HeritageScopeValidationError(f"{slug} source artifact identity or hash mismatch")
        scope_file = root / scope_path
        scope = _load_json(scope_file)
        scope["review_inventory"] = build_review_inventory(slug, export, source_path.name, sha256)
        scope["summary"]["review_inventory_point_count"] = len(scope["review_inventory"]["records"])
        scope_file.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HeritageScopeValidationError(f"cannot parse JSON {path}: {exc}") from exc


def _error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _repo_file(root: Path, value: Any, errors: list[str], label: str) -> None:
    if not isinstance(value, str):
        errors.append(f"{label} must be a repository path")
        return
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "\\" in value:
        errors.append(f"{label} must be a relative POSIX repository path")
    elif not root.joinpath(*posix.parts).is_file():
        errors.append(f"{label} does not exist: {value}")


def _validate_inventory(slug: str, inventory: Any, errors: list[str]) -> None:
    label = f"scope {slug} review_inventory"
    expected = INVENTORY_EXPECTED[slug]
    if not isinstance(inventory, dict):
        errors.append(f"{label} must be an object")
        return
    _error(errors, inventory.get("status") == "REVIEW_ONLY_POINT_INVENTORY_NOT_RUNTIME_SOURCE", f"{label} must remain review-only")
    _error(errors, inventory.get("boundary_authority") is False, f"{label} must not claim boundary authority")
    provenance = inventory.get("source_provenance", {})
    _error(errors, provenance.get("source_database") == "points_world_heritage.gdb", f"{label} source database mismatch")
    _error(errors, provenance.get("source_layer") == expected["source_layer"], f"{label} source layer mismatch")
    _error(errors, provenance.get("source_artifact_basename") == expected["artifact_basename"], f"{label} artifact basename mismatch")
    _error(errors, provenance.get("source_artifact_sha256") == expected["sha256"], f"{label} source hash mismatch")
    _error(errors, provenance.get("source_record_count") == expected["record_count"], f"{label} source count mismatch")
    _error(errors, provenance.get("source_geometry_type") == "esriGeometryPoint", f"{label} source geometry must be esriGeometryPoint")
    _error(errors, provenance.get("source_wkid") == 4326, f"{label} source WKID must be 4326")
    _error(errors, provenance.get("source_field_names") == expected["fields"], f"{label} source field schema mismatch")
    _error(errors, provenance.get("extraction_date") == "2026-08-22", f"{label} extraction date mismatch")
    _error(errors, provenance.get("absolute_source_path_recorded") is False, f"{label} must not record an absolute path")
    _error(errors, "C:\\" not in json.dumps(provenance, ensure_ascii=False), f"{label} contains a Windows path")

    records = inventory.get("records", [])
    _error(errors, isinstance(records, list) and len(records) == expected["record_count"], f"{label} record count mismatch")
    if not isinstance(records, list):
        return
    ids: list[Any] = []
    names: list[str] = []
    coordinates: list[tuple[float, float]] = []
    for index, record in enumerate(records):
        record_label = f"{label} record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{record_label} must be an object")
            continue
        attributes = record.get("source_attributes", {})
        geometry = record.get("source_geometry", {})
        _error(errors, list(attributes) == expected["fields"], f"{record_label} does not preserve the exact source fields")
        _error(errors, record.get("destination_slug") == slug, f"{record_label} destination linkage mismatch")
        _error(errors, record.get("source_database") == "points_world_heritage.gdb" and record.get("source_layer") == expected["source_layer"], f"{record_label} source identity mismatch")
        _error(errors, record.get("source_artifact_basename") == expected["artifact_basename"], f"{record_label} source artifact mismatch")
        longitude, latitude = geometry.get("longitude"), geometry.get("latitude")
        _error(errors, geometry.get("geometry_type") == "Point" and geometry.get("wkid") == 4326, f"{record_label} must be a WKID 4326 Point")
        _error(errors, _valid_number(longitude) and _valid_number(latitude), f"{record_label} coordinates must be finite")
        if _valid_number(longitude) and _valid_number(latitude):
            _error(errors, 9.0 <= longitude <= 25.5 and 19.0 <= latitude <= 34.0, f"{record_label} coordinates are outside Libya bounds")
            coordinates.append((longitude, latitude))
        if slug == "sabratha" and _valid_number(longitude) and _valid_number(latitude):
            _error(errors, abs(longitude - attributes.get("X", math.inf)) <= 1e-6 and abs(latitude - attributes.get("Y", math.inf)) <= 1e-6, f"{record_label} geometry does not match X/Y")
        name_field = "name" if slug == "leptis-magna" else "اسم_ا"
        _error(errors, record.get("source_name") == attributes.get(name_field), f"{record_label} source name was not preserved")
        names.append((attributes.get(name_field) or "").strip())
        classification = record.get("review_classification")
        _error(errors, classification in REVIEW_CLASSIFICATIONS, f"{record_label} has unsupported review classification")
        _error(errors, isinstance(record.get("classification_basis"), str) and bool(record.get("classification_basis")), f"{record_label} lacks classification evidence")
        _error(errors, isinstance(record.get("quality_flags"), list) and record.get("quality_flags") == sorted(set(record.get("quality_flags", []))), f"{record_label} quality flags are not deterministic")
        for field in ("canonical_approval", "publication_approved", "public_visibility_enabled"):
            _error(errors, record.get(field) is False, f"{record_label} {field} must remain false")
        _error(errors, record.get("institutional_review_status") == "UNRESOLVED", f"{record_label} institutional review must remain unresolved")
        identity_payload = {
            "source_database": "points_world_heritage.gdb",
            "source_layer": expected["source_layer"],
            "source_attributes": attributes,
            "geometry": {"x": longitude, "y": latitude, "wkid": 4326},
        }
        digest = hashlib.sha256(json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
        expected_id = f"heritage-review-{slug}-{digest}"
        _error(errors, record.get("review_feature_id") == expected_id, f"{record_label} deterministic identity mismatch")
        ids.append(record.get("review_feature_id"))
    _error(errors, len(ids) == len(set(ids)), f"{label} deterministic IDs must be unique")

    quality = inventory.get("quality_summary", {})
    required_quality = (
        {"record_count": 51, "unique_nonblank_name_count": 49, "blank_popupinfo_count": 49, "blank_en_name_count": 33, "blank_photo_count": 42, "parseable_photo_attachment_json_count": 4, "truncated_photo_attachment_json_count": 5}
        if slug == "leptis-magna"
        else {"record_count": 39, "unique_nonblank_name_count": 36, "unique_coordinate_count": 39, "blank_description_count": 39, "geometry_xy_match_within_tolerance_count": 39}
    )
    for field, value in required_quality.items():
        _error(errors, quality.get(field) == value, f"{label} quality finding {field} mismatch")
    _error(errors, sum(inventory.get("classification_counts", {}).values()) == expected["record_count"], f"{label} classification counts mismatch")
    _error(errors, set(inventory.get("classification_counts", {})) == REVIEW_CLASSIFICATIONS, f"{label} classification count vocabulary mismatch")

    by_name = {name: [item for item in records if (item.get("source_name") or "").strip() == name] for name in set(names)}
    if slug == "leptis-magna":
        _error(errors, len(by_name.get("متحف الفسيفساء", [])) == 2 and all("DUPLICATE_EXACT_NAME_AND_COORDINATE_REVIEW" in item["quality_flags"] for item in by_name["متحف الفسيفساء"]), f"{label} mosaic museum duplicate is not flagged")
        for name in ("معبد جوبيتير دوليكينوس", "معبد جوبيتير"):
            _error(errors, all("EXACT_COORDINATE_IDENTITY_CONFLICT_REVIEW" in item["quality_flags"] for item in by_name.get(name, [])), f"{label} Jupiter coordinate conflict is not flagged")
        zero_records = [item for item in records if item["source_attributes"].get("objectid") == 0]
        _error(errors, len(zero_records) == 2 and all("NON_UNIQUE_MUTABLE_OBJECTID_REVIEW" in item["quality_flags"] for item in zero_records), f"{label} duplicate objectid zero is not flagged")
        _error(errors, all("ATTACHMENT_JSON_IN_EN_NAME_FIELD_REVIEW" in item["quality_flags"] for item in by_name.get("قوس الإمبراطور تراجان", [])), f"{label} en_name attachment JSON is not flagged")
        _error(errors, all("MEDIA_IDENTITY_CONFLICT_REVIEW" in item["quality_flags"] for item in by_name.get("قوس سبتيموس سفيروس", [])), f"{label} media identity conflict is not flagged")
    else:
        for name in ("معبد سيرابيس", "حوض المعمودية", "معبد ايزيس وإيزوريس"):
            _error(errors, len(by_name.get(name, [])) == 2 and all("REPEATED_NAME_DISTINCT_COORDINATES_REVIEW" in item["quality_flags"] for item in by_name[name]), f"{label} repeated name {name} is not flagged")
        incomplete = by_name.get("Serapaeum (Sabratha", [])
        _error(errors, len(incomplete) == 1 and incomplete[0].get("proposed_normalized_name") == "Serapaeum (Sabratha)" and "INCOMPLETE_SOURCE_NAME_REVIEW" in incomplete[0]["quality_flags"], f"{label} incomplete Serapaeum name review is missing")
        for name in ("حمامات أوفانيوس", "حمامات ريجيو السابع"):
            _error(errors, all("NEARBY_DISTINCT_NAMES_REVIEW" in item["quality_flags"] for item in by_name.get(name, [])), f"{label} nearby baths review is missing")


def validate_scope_payloads(
    scopes: list[dict[str, Any]],
    coordinates: dict[str, Any],
    canonical_review: dict[str, Any],
    registry: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> None:
    """Validate scope documents against existing reviewed coordinate evidence."""
    errors: list[str] = []
    _error(errors, len(scopes) == 2, "exactly two scope artifacts are required")
    slugs = [scope.get("canonical_destination_slug") for scope in scopes if isinstance(scope, dict)]
    ids = [scope.get("scope_id") for scope in scopes if isinstance(scope, dict)]
    _error(errors, slugs == ["leptis-magna", "sabratha"], "scope artifacts must use deterministic canonical-slug order")
    _error(errors, len(ids) == len(set(ids)), "duplicate scope ID")

    coordinate_by_slug = {item.get("slug"): item for item in coordinates.get("records", []) if isinstance(item, dict)}
    review_by_slug = {item.get("slug"): item for item in canonical_review.get("destinations", []) if isinstance(item, dict)}
    registry_by_slug = {
        item.get("current_canonical_slug"): item
        for item in (registry or {}).get("records", [])
        if isinstance(item, dict)
    }

    for scope in scopes:
        if not isinstance(scope, dict):
            errors.append("scope artifact must be an object")
            continue
        slug = scope.get("canonical_destination_slug")
        label = f"scope {slug}"
        expected = EXPECTED.get(slug)
        if expected is None:
            errors.append(f"{label} uses unsupported canonical slug")
            continue
        for field in ("schema_version", "scope_id", "registry_record_id", "name_ar", "name_en", "entity_type", "development_priority_tier", "project_identity_status", "source_policy", "provenance", "site_anchor", "boundary", "layer_taxonomy", "candidate_features", "review_inventory", "media_evidence", "data_gaps", "institutional_actions_required", "publication_governance", "summary"):
            _error(errors, field in scope, f"{label} missing {field}")
        _error(errors, scope.get("schema_version") == 1, f"{label} has unsupported schema_version")
        for field in ("scope_id", "registry_record_id", "name_ar", "name_en"):
            _error(errors, scope.get(field) == expected[field], f"{label} has incorrect {field}")
        _error(errors, scope.get("entity_type") == "ARCHAEOLOGICAL_HERITAGE_SITE", f"{label} has unsupported entity type")
        _error(errors, scope.get("development_priority_tier") == "PRIMARY", f"{label} must remain PRIMARY")
        _error(errors, scope.get("project_identity_status") == "REPOSITORY_IDENTITY_CONFIRMED", f"{label} has unsupported identity status")

        policy = scope.get("source_policy", {})
        _error(errors, policy.get("status") == "REVIEW_ONLY_NOT_PUBLICATION_APPROVAL", f"{label} must be review-only")
        _error(errors, policy.get("repository_evidence_only") is True and policy.get("external_inference_allowed") is False, f"{label} source policy permits inference")

        anchor = scope.get("site_anchor", {})
        longitude, latitude = anchor.get("longitude"), anchor.get("latitude")
        _error(errors, _valid_number(longitude) and _valid_number(latitude), f"{label} anchor coordinates must be finite numeric values")
        if _valid_number(longitude) and _valid_number(latitude):
            _error(errors, 9.0 <= longitude <= 25.5 and 19.0 <= latitude <= 34.0, f"{label} anchor coordinates are outside Libya bounds")
        _error(errors, anchor.get("anchor_role") == "REVIEWED_CANONICAL_DESTINATION_SITE_ANCHOR", f"{label} anchor has unsupported or relabeled role")
        _error(errors, anchor.get("geometry_type") == "Point", f"{label} anchor must be a Point")
        _error(errors, anchor.get("review_status") == "REVIEWED_AUTHORITATIVE_PAIR", f"{label} anchor review status is invalid")
        _error(errors, anchor.get("source_path") == COORDINATES_PATH.as_posix(), f"{label} anchor source path is incorrect")
        _error(errors, anchor.get("evidence_identifier") == f"slug:{slug}", f"{label} anchor evidence identifier is incorrect")
        _error(errors, anchor.get("source_reference") == expected["source_reference"], f"{label} anchor source reference is incorrect")
        for claim in ("is_representative_display_point", "is_boundary_centroid", "is_entrance", "is_visitor_facility", "publication_approved"):
            _error(errors, anchor.get(claim) is False, f"{label} anchor must not claim {claim}")
        reviewed = coordinate_by_slug.get(slug, {})
        _error(errors, reviewed.get("longitude") == expected["longitude"] and reviewed.get("latitude") == expected["latitude"], f"{label} authoritative coordinate evidence changed")
        _error(errors, longitude == reviewed.get("longitude") and latitude == reviewed.get("latitude"), f"{label} anchor does not preserve the reviewed coordinate pair")
        _error(errors, reviewed.get("source_reference") == expected["source_reference"] and reviewed.get("status") == "reviewed", f"{label} reviewed coordinate provenance is incorrect")
        best = review_by_slug.get(slug, {}).get("best_candidate", {})
        _error(errors, best.get("source_feature_id") == expected["source_feature_id"], f"{label} canonical-review source identity changed")
        _error(errors, best.get("longitude") == longitude and best.get("latitude") == latitude, f"{label} canonical-review coordinate mismatch")

        provenance = scope.get("provenance", {})
        coordinate_source = provenance.get("coordinate_source", {})
        review_source = provenance.get("coordinate_review_source", {})
        _error(errors, coordinate_source.get("path") == COORDINATES_PATH.as_posix(), f"{label} coordinate provenance path is incorrect")
        _error(errors, coordinate_source.get("evidence_identifier") == f"slug:{slug}", f"{label} coordinate provenance identifier is incorrect")
        _error(errors, coordinate_source.get("source_reference") == expected["source_reference"], f"{label} coordinate provenance reference is incorrect")
        _error(errors, review_source.get("path") == CANONICAL_REVIEW_PATH.as_posix(), f"{label} canonical-review provenance path is incorrect")
        _error(errors, review_source.get("evidence_identifier") == f"source_feature_id:{expected['source_feature_id']}", f"{label} canonical-review provenance identifier is incorrect")
        _error(errors, provenance.get("provenance_complete_for_scope") is True and provenance.get("provenance_complete_for_detailed_layer") is False, f"{label} overstates detailed-layer provenance")

        boundary = scope.get("boundary", {})
        _error(errors, boundary.get("status") == "AUTHORITATIVE_BOUNDARY_REQUIRED", f"{label} has unsupported boundary status")
        _error(errors, boundary.get("geometry_present") is False, f"{label} contains fabricated boundary geometry")
        _error(errors, boundary.get("geometry_type") is None and boundary.get("source") is None, f"{label} boundary geometry or source must remain null")
        _error(errors, boundary.get("review_required") is True, f"{label} boundary must require review")

        taxonomy = scope.get("layer_taxonomy", [])
        categories = [item.get("category") for item in taxonomy if isinstance(item, dict)]
        _error(errors, categories == list(TAXONOMY), f"{label} taxonomy is unsupported or non-deterministic")
        for item in taxonomy:
            if not isinstance(item, dict):
                errors.append(f"{label} taxonomy entry must be an object")
                continue
            types = item.get("allowable_geometry_types")
            _error(errors, isinstance(types, list) and bool(types) and all(value in GEOMETRY_TYPES for value in types), f"{label} taxonomy has invalid geometry type")
            _error(errors, item.get("authoritative_features_present") is False, f"{label} taxonomy falsely claims authoritative features")
            _error(errors, isinstance(item.get("required_evidence"), str) and bool(item.get("required_evidence")), f"{label} taxonomy lacks required evidence")
            _error(errors, item.get("human_review_required") is True and item.get("institutional_review_required") is True, f"{label} taxonomy must require review")

        candidates = scope.get("candidate_features", [])
        _error(errors, isinstance(candidates, list), f"{label} candidate_features must be an array")
        source_ids: list[Any] = []
        if isinstance(candidates, list):
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    errors.append(f"{label} candidate must be an object")
                    continue
                source_id = candidate.get("source_feature_id")
                source_ids.append(source_id)
                _error(errors, isinstance(source_id, (str, int)) and not isinstance(source_id, bool), f"{label} candidate lacks source identity")
                _error(errors, candidate.get("destination_slug") == slug, f"{label} candidate destination linkage is invalid")
                _error(errors, candidate.get("feature_category") in TAXONOMY, f"{label} candidate has unsupported classification")
                _error(errors, isinstance(candidate.get("source_path"), str) and isinstance(candidate.get("selection_reason"), str) and bool(candidate.get("selection_reason")), f"{label} candidate lacks evidence")
                if isinstance(candidate.get("source_path"), str):
                    _repo_file(root, candidate["source_path"], errors, f"{label} candidate source")
                _error(errors, candidate.get("publication_approved") is False, f"{label} candidate grants publication approval")
                _error(errors, candidate.get("review_required") is True, f"{label} candidate must require review")
        _error(errors, len(source_ids) == len(set(source_ids)), f"{label} has duplicate candidate source ID")

        for media in scope.get("media_evidence", []):
            _repo_file(root, media.get("repository_path"), errors, f"{label} media path")
            _error(errors, media.get("evidence_role") == "IDENTITY_AND_VISITOR_PRESENTATION_ONLY", f"{label} media has unsupported evidence role")
            _error(errors, media.get("grants_spatial_authority") is False and media.get("grants_archaeological_classification") is False, f"{label} media grants coordinate or archaeological authority")

        governance = scope.get("publication_governance", {})
        _error(errors, governance.get("status") == "REVIEW_ONLY_NOT_PUBLICATION_APPROVAL", f"{label} governance status is invalid")
        for field in ("runtime_source", "runtime_eligible", "grants_institutional_approval", "grants_publication_eligibility", "publication_approved"):
            _error(errors, governance.get(field) is False, f"{label} governance field {field} must remain false")
        _error(errors, governance.get("approval_event_reference") is None, f"{label} must not reference an approval event")
        summary = scope.get("summary", {})
        _error(errors, summary.get("site_anchor_count") == 1 and summary.get("candidate_feature_count") == len(candidates), f"{label} summary counts are invalid")
        _validate_inventory(slug, scope.get("review_inventory"), errors)
        inventory_records = scope.get("review_inventory", {}).get("records", []) if isinstance(scope.get("review_inventory"), dict) else []
        _error(errors, summary.get("review_inventory_point_count") == len(inventory_records), f"{label} review inventory summary count is invalid")
        _error(errors, summary.get("authoritative_boundary_present") is False and summary.get("detailed_gis_layer_created") is False and summary.get("scope_contract_only") is True, f"{label} falsely claims detailed GIS coverage")

        if registry is not None:
            record = registry_by_slug.get(slug, {})
            _error(errors, record.get("registry_record_id") == expected["registry_record_id"], f"{label} registry identity mismatch")
            _error(errors, record.get("development_priority_tier") == "PRIMARY", f"{label} registry priority changed")
            _error(errors, record.get("gis_scope_contract_present") is True, f"{label} registry lacks scope-contract status")
            _error(errors, record.get("gis_scope_contract_path") == next(path.as_posix() for path in SCOPE_PATHS if slug in path.name), f"{label} registry scope path mismatch")
            _error(errors, record.get("gis_layer_present") is False and record.get("gis_record_count") == 0, f"{label} scope contract is counted as a detailed GIS layer")

    if errors:
        raise HeritageScopeValidationError("\n".join(errors))


def validate_serialization(paths: list[Path]) -> None:
    errors: list[str] = []
    for path in paths:
        raw = path.read_bytes()
        _error(errors, not raw.startswith(b"\xef\xbb\xbf"), f"{path} must be UTF-8 without BOM")
        _error(errors, raw.endswith(b"\n") and not raw.endswith(b"\n\n"), f"{path} must have exactly one final newline")
        _error(errors, b"\r\n" not in raw, f"{path} must use LF newlines")
    if errors:
        raise HeritageScopeValidationError("\n".join(errors))


def validate_repository(root: Path = ROOT, scope_paths: tuple[Path, ...] = SCOPE_PATHS, check_git: bool = True) -> dict[str, Any]:
    """Validate committed evidence and review contracts without writing files."""
    resolved = [root / path for path in scope_paths]
    missing = [path.as_posix() for path, full in zip(scope_paths, resolved) if not full.is_file()]
    if missing:
        raise HeritageScopeValidationError(f"missing scope artifact(s): {', '.join(missing)}")
    validate_serialization(resolved)
    scopes = [_load_json(path) for path in resolved]
    coordinates = _load_json(root / COORDINATES_PATH)
    canonical_review = _load_json(root / CANONICAL_REVIEW_PATH)
    registry = _load_json(root / REGISTRY_PATH)
    validate_scope_payloads(scopes, coordinates, canonical_review, registry, root)
    if len(registry.get("records", [])) != 15:
        raise HeritageScopeValidationError("registry must remain exactly 15 records")
    priorities = [item.get("development_priority_tier") for item in registry["records"]]
    if priorities.count("PRIMARY") != 9 or priorities.count("COMPLEMENTARY") != 6:
        raise HeritageScopeValidationError("registry priority distribution changed")
    scoped_count = sum(item.get("gis_record_count", 0) for item in registry["records"])
    if scoped_count != 214:
        raise HeritageScopeValidationError("existing scoped GIS count must remain 214")
    ledger = (root / LEDGER_PATH).read_bytes()
    if ledger:
        raise HeritageScopeValidationError("approval ledger must remain empty")
    natural_text = (root / NATURAL_LAYER_PATH).read_text(encoding="utf-8")
    for heritage_id in (832, 913):
        if f"sourceFeatureId: {heritage_id}" in natural_text or f'"source_feature_id": {heritage_id}' in natural_text:
            raise HeritageScopeValidationError(f"heritage ID {heritage_id} leaked into natural public layer")
    if check_git:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", *sorted(PROTECTED_PATHS)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        changed = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
        if changed:
            raise HeritageScopeValidationError(f"protected artifacts changed: {', '.join(changed)}")
    inventory_count = sum(len(item["review_inventory"]["records"]) for item in scopes)
    if inventory_count != 90:
        raise HeritageScopeValidationError("review inventory total must remain 90")
    return {"scope_count": 2, "candidate_feature_count": sum(len(item["candidate_features"]) for item in scopes), "review_inventory_point_count": inventory_count, "scoped_gis_record_count": scoped_count}


def main() -> int:
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "import-inventories":
            import_review_inventories(Path(sys.argv[2]), Path(sys.argv[3]))
        elif len(sys.argv) != 1:
            raise HeritageScopeValidationError("usage: primary_heritage_gis_review.py [import-inventories LEPTIS_JSON SABRATHA_JSON]")
        summary = validate_repository()
    except (HeritageScopeValidationError, OSError, subprocess.SubprocessError) as exc:
        print(f"Primary heritage GIS review validation failed:\n{exc}", file=sys.stderr)
        return 1
    print("Primary heritage GIS review validation passed: " + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
