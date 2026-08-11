from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.destination_import import ImportDataset, load_dataset

MAX_SOURCE_BYTES = 25 * 1024 * 1024
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
LATIN_RE = re.compile(r"[A-Za-z]")
SPACE_RE = re.compile(r"\s+")
AGGREGATE_SLUGS = {"acacus", "green-mountain", "desert", "nafusa"}


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    expected_filename: str = Field(min_length=1, max_length=255)
    format: Literal["kml", "geojson", "json"]
    title: str
    dataset_role: str
    source_scope: str


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    organization: str
    sources: list[SourceSpec]

    @model_validator(mode="after")
    def unique_sources(self) -> "SourceManifest":
        ids = [item.source_id for item in self.sources]
        names = [item.expected_filename for item in self.sources]
        if len(ids) != len(set(ids)) or len(names) != len(set(names)):
            raise ValueError("source IDs and expected filenames must be unique")
        return self


@dataclass
class NormalizedFeature:
    source_id: str
    feature_id: str
    source_feature_id: str | None
    id_kind: str
    source_index: int
    raw_name: str | None
    name_ar: str | None
    name_en: str | None
    description: str | None
    category: str | None
    region: str | None
    locality: str | None
    context_path: list[str]
    geometry_types: list[str]
    latitude: float | None
    longitude: float | None
    source_reference: str
    media: list[str]
    properties: dict[str, Any]
    related_sources: list[str] = field(default_factory=list)


@dataclass
class SourceAudit:
    source_id: str
    file_name: str
    format: str
    parse_status: str
    sha256: str | None = None
    size_bytes: int | None = None
    encoding: str | None = None
    feature_count: int = 0
    record_count: int = 0
    geometry_types: dict[str, int] = field(default_factory=dict)
    coordinate_dimensions: dict[str, int] = field(default_factory=dict)
    bbox: list[float] | None = None
    property_keys: list[str] = field(default_factory=list)
    arabic_names: int = 0
    english_names: int = 0
    descriptions: int = 0
    categories: int = 0
    source_references: int = 0
    media_features: int = 0
    stable_native_ids: int = 0
    duplicate_feature_ids: int = 0
    duplicate_names: int = 0
    duplicate_name_coordinates: int = 0
    missing_names: int = 0
    missing_geometries: int = 0
    malformed_features: int = 0
    invalid_coordinates: int = 0
    warnings: list[str] = field(default_factory=list)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_manifest(path: Path) -> SourceManifest:
    return SourceManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def safe_source_path(source_dir: Path, filename: str) -> Path:
    root = source_dir.resolve(strict=True)
    candidate = (root / filename).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"source path escapes source directory: {filename}")
    return candidate


def _read_source(path: Path) -> tuple[bytes, str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError(f"source exceeds {MAX_SOURCE_BYTES} bytes")
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("source must be UTF-8") from exc
    return raw, sha256_bytes(raw)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _first_child(element: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in element if _local_name(child.tag) == name), None)


def _classify_name(raw_name: str | None) -> tuple[str | None, str | None]:
    if not raw_name:
        return None, None
    has_arabic, has_latin = bool(ARABIC_RE.search(raw_name)), bool(LATIN_RE.search(raw_name))
    return (raw_name if has_arabic and not has_latin else None, raw_name if has_latin and not has_arabic else None)


def _finite_pair(longitude: Any, latitude: Any) -> tuple[float, float] | None:
    if isinstance(longitude, bool) or isinstance(latitude, bool):
        return None
    try:
        lon, lat = float(longitude), float(latitude)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lon) or not math.isfinite(lat) or not -180 <= lon <= 180 or not -90 <= lat <= 90:
        return None
    return lon, lat


def _kml_coordinates(text: str | None) -> tuple[list[tuple[float, float]], Counter[str], int]:
    valid: list[tuple[float, float]] = []
    dimensions: Counter[str] = Counter()
    invalid = 0
    for token in (text or "").replace("\n", " ").split():
        parts = token.split(",")
        dimensions[str(len(parts))] += 1
        if len(parts) < 2:
            invalid += 1
            continue
        pair = _finite_pair(parts[0], parts[1])
        if pair is None:
            invalid += 1
        else:
            valid.append(pair)
    return valid, dimensions, invalid


def parse_kml(spec: SourceSpec, path: Path) -> tuple[list[NormalizedFeature], SourceAudit]:
    raw, digest = _read_source(path)
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DTD and entity declarations are forbidden")
    root = ET.fromstring(raw)
    features: list[NormalizedFeature] = []
    audit = SourceAudit(spec.source_id, path.name, "kml", "parsed", digest, len(raw), "UTF-8")
    property_keys: set[str] = set()
    geometry_counts: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    all_points: list[tuple[float, float]] = []
    placemarks = [item for item in root.iter() if _local_name(item.tag) == "Placemark"]
    parents = {child: parent for parent in root.iter() for child in parent}
    for index, placemark in enumerate(placemarks, 1):
        name = _text(_first_child(placemark, "name"))
        description = _text(_first_child(placemark, "description"))
        properties: dict[str, Any] = {}
        for item in placemark.iter():
            kind = _local_name(item.tag)
            if kind == "Data" and item.get("name"):
                properties[item.get("name", "")] = _text(_first_child(item, "value"))
            elif kind == "SimpleData" and item.get("name"):
                properties[item.get("name", "")] = _text(item)
        property_keys.update(properties)
        geometry_types: list[str] = []
        point_pair: tuple[float, float] | None = None
        geometry_elements = [item for item in placemark.iter() if _local_name(item.tag) in {"Point", "LineString", "Polygon", "MultiGeometry"}]
        for geometry in geometry_elements:
            kind = _local_name(geometry.tag)
            geometry_types.append(kind)
            geometry_counts[kind] += 1
            if kind == "Point":
                coordinate_node = next((item for item in geometry.iter() if _local_name(item.tag) == "coordinates"), None)
                coords, dims, invalid = _kml_coordinates(_text(coordinate_node))
                dimensions.update(dims); audit.invalid_coordinates += invalid
                if len(coords) == 1 and point_pair is None:
                    point_pair = coords[0]
                    all_points.append(coords[0])
        native_id = placemark.get("id") or next((str(properties[key]) for key in properties if key.lower() in {"id", "feature_id", "attraction_id", "atlas_id"} and properties[key]), None)
        fingerprint = sha256_bytes(spec.source_id.encode() + b"\0" + ET.tostring(placemark, encoding="utf-8"))
        feature_id = native_id or f"fp-{fingerprint[:24]}"
        lower_properties = {key.lower(): value for key, value in properties.items()}
        classified_ar, classified_en = _classify_name(name)
        name_ar = next((lower_properties[key] for key in ("name_ar", "arabic_name", "الاسم") if lower_properties.get(key)), classified_ar)
        name_en = next((lower_properties[key] for key in ("name_en", "en_name", "english_name", "الاسم باللغة الانجليزية") if lower_properties.get(key)), classified_en)
        category = next((lower_properties[key] for key in ("category", "type", "classification", "class", "category_التصنيف", "التصنيف", "الفئة", "النوع") if lower_properties.get(key)), None)
        region = next((lower_properties[key] for key in ("region", "district", "region_المنطقة", "الاقليم السياحي") if lower_properties.get(key)), None)
        locality = next((lower_properties[key] for key in ("locality", "city", "municipality", "المدينة", "البلدية", "البلدية_municipality", "المدينـــة") if lower_properties.get(key)), None)
        media = [str(value) for key, value in properties.items() if value and any(token in key.lower() for token in ("image", "photo", "media"))]
        context_path: list[str] = []
        ancestor = parents.get(placemark)
        while ancestor is not None:
            if _local_name(ancestor.tag) in {"Folder", "Document"}:
                context_name = _text(_first_child(ancestor, "name"))
                if context_name:
                    context_path.append(context_name)
            ancestor = parents.get(ancestor)
        context_path.reverse()
        features.append(NormalizedFeature(
            spec.source_id, feature_id, native_id, "native" if native_id else "registry_fingerprint", index,
            name, str(name_ar).strip() if name_ar else None, str(name_en).strip() if name_en else None, description, str(category) if category else None,
            str(region) if region else None, str(locality) if locality else None, context_path,
            sorted(set(geometry_types)), point_pair[1] if point_pair else None,
            point_pair[0] if point_pair else None, f"{spec.expected_filename}#Placemark-{index}", media, properties,
        ))
    audit.geometry_types = dict(sorted(geometry_counts.items()))
    audit.coordinate_dimensions = dict(sorted(dimensions.items()))
    audit.property_keys = sorted(property_keys)
    _finish_audit(audit, features, all_points)
    return features, audit


def _property(properties: dict[str, Any], *names: str) -> Any:
    lowered = {str(key).lower(): value for key, value in properties.items()}
    return next((lowered[name] for name in names if lowered.get(name) not in (None, "")), None)


def parse_geojson(spec: SourceSpec, path: Path) -> tuple[list[NormalizedFeature], SourceAudit]:
    raw, digest = _read_source(path)
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise ValueError("GeoJSON must be a FeatureCollection with a features array")
    features: list[NormalizedFeature] = []
    audit = SourceAudit(spec.source_id, path.name, "geojson", "parsed", digest, len(raw), "UTF-8")
    property_keys: set[str] = set(); geometry_counts: Counter[str] = Counter(); all_points: list[tuple[float, float]] = []
    for index, feature in enumerate(document["features"], 1):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            audit.malformed_features += 1; continue
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            audit.malformed_features += 1; properties = {}
        property_keys.update(map(str, properties))
        geometry = feature.get("geometry")
        geometry_type = geometry.get("type") if isinstance(geometry, dict) else None
        geometry_types = [geometry_type] if isinstance(geometry_type, str) else []
        if geometry_type: geometry_counts[geometry_type] += 1
        pair = None
        if geometry_type == "Point":
            coordinates = geometry.get("coordinates")
            if isinstance(coordinates, list):
                audit.coordinate_dimensions[str(len(coordinates))] = audit.coordinate_dimensions.get(str(len(coordinates)), 0) + 1
                if len(coordinates) >= 2: pair = _finite_pair(coordinates[0], coordinates[1])
            if pair is None: audit.invalid_coordinates += 1
            else: all_points.append(pair)
        raw_name = _property(properties, "name", "title", "name_ar", "name_en")
        raw_name = str(raw_name).strip() if raw_name is not None else None
        name_ar = _property(properties, "name_ar", "arabic_name")
        name_en = _property(properties, "name_en", "english_name")
        classified_ar, classified_en = _classify_name(raw_name)
        name_ar = str(name_ar).strip() if name_ar else classified_ar
        name_en = str(name_en).strip() if name_en else classified_en
        native_id = feature.get("id") or _property(properties, "feature_id", "id", "attraction_id")
        fingerprint = sha256_bytes(spec.source_id.encode() + b"\0" + json.dumps(feature, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        feature_id = str(native_id) if native_id is not None else f"fp-{fingerprint[:24]}"
        media_values: list[str] = []
        for key, value in properties.items():
            if any(token in str(key).lower() for token in ("image", "photo", "media")) and value not in (None, "", []):
                media_values.extend(str(item) for item in value) if isinstance(value, list) else media_values.append(str(value))
        raw_folders = properties.get("folders")
        context_path = [str(item) for item in raw_folders] if isinstance(raw_folders, list) else ([str(raw_folders)] if raw_folders else [])
        features.append(NormalizedFeature(
            spec.source_id, feature_id, str(native_id) if native_id is not None else None,
            "native" if native_id is not None else "registry_fingerprint", index, raw_name,
            name_ar, name_en, str(_property(properties, "description", "desc") or "") or None,
            str(_property(properties, "category_enriched", "primary_category", "category", "type", "classification") or "") or None,
            str(_property(properties, "region_ar", "region", "district") or "") or None,
            str(_property(properties, "locality_ar", "locality", "city", "municipality") or "") or None, context_path,
            geometry_types, pair[1] if pair else None, pair[0] if pair else None,
            f"{spec.expected_filename}#Feature-{index}", media_values, properties,
        ))
    audit.geometry_types = dict(sorted(geometry_counts.items())); audit.property_keys = sorted(property_keys)
    _finish_audit(audit, features, all_points)
    return features, audit


def parse_json_registry(spec: SourceSpec, path: Path) -> tuple[list[NormalizedFeature], SourceAudit]:
    raw, digest = _read_source(path)
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, list) or any(not isinstance(item, dict) for item in document):
        raise ValueError("supplementary JSON registry must be an array of objects")
    keys = sorted({str(key) for item in document for key in item})
    native_ids = [str(item["runtime_id"]) for item in document if item.get("runtime_id")]
    counts = Counter(native_ids)
    audit = SourceAudit(
        spec.source_id, path.name, "json", "parsed", digest, len(raw), "UTF-8",
        record_count=len(document), property_keys=keys, stable_native_ids=len(native_ids),
        duplicate_feature_ids=sum(count - 1 for count in counts.values() if count > 1),
        warnings=["supplementary governance records are audited but not normalized as geographic features"],
    )
    return [], audit


def _finish_audit(audit: SourceAudit, features: list[NormalizedFeature], points: list[tuple[float, float]]) -> None:
    audit.feature_count = len(features)
    audit.arabic_names = sum(bool(item.name_ar) for item in features)
    audit.english_names = sum(bool(item.name_en) for item in features)
    audit.descriptions = sum(bool(item.description) for item in features)
    audit.categories = sum(bool(item.category) for item in features)
    audit.source_references = sum(bool(item.source_reference) for item in features)
    audit.media_features = sum(bool(item.media) for item in features)
    audit.stable_native_ids = sum(item.id_kind == "native" for item in features)
    audit.missing_names = sum(not item.raw_name and not item.name_ar and not item.name_en for item in features)
    audit.missing_geometries = sum(not item.geometry_types for item in features)
    ids = Counter(item.feature_id for item in features); audit.duplicate_feature_ids = sum(count - 1 for count in ids.values() if count > 1)
    names = Counter(normalize_name(item.raw_name) for item in features if item.raw_name); audit.duplicate_names = sum(count - 1 for count in names.values() if count > 1)
    named_points = Counter((normalize_name(item.raw_name), item.longitude, item.latitude) for item in features if item.raw_name and item.latitude is not None)
    audit.duplicate_name_coordinates = sum(count - 1 for count in named_points.values() if count > 1)
    if points:
        longitudes, latitudes = [item[0] for item in points], [item[1] for item in points]
        audit.bbox = [min(longitudes), min(latitudes), max(longitudes), max(latitudes)]


def normalize_name(value: str | None) -> str:
    return SPACE_RE.sub(" ", (value or "").strip().casefold())


def canonical_destinations(dataset: ImportDataset) -> list[dict[str, Any]]:
    output = []
    for item in dataset.records:
        translations = {entry.language_code: entry.name for entry in item.translations}
        output.append({
            "slug": item.slug, "name_ar": translations.get("ar"), "name_en": translations.get("en"),
            "category": item.category, "region": item.region, "latitude": item.latitude, "longitude": item.longitude,
            "aggregate": item.slug in AGGREGATE_SLUGS,
        })
    return output


def build_candidates(canonical: list[dict[str, Any]], features: list[NormalizedFeature], specs: dict[str, SourceSpec]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    candidates: list[dict[str, Any]] = []
    matched_slugs: set[str] = set()
    for destination in canonical:
        expected = {normalize_name(destination["name_ar"]), normalize_name(destination["name_en"]), normalize_name(destination["slug"])} - {""}
        for feature in features:
            source_names = {normalize_name(feature.raw_name), normalize_name(feature.name_ar), normalize_name(feature.name_en)} - {""}
            slug_property = next((str(value) for key, value in feature.properties.items() if key.lower() in {"slug", "destination_slug"} and value), None)
            if slug_property == destination["slug"]:
                state, reason = "EXACT_ID", "source property exactly equals canonical destination slug"
            elif expected & source_names:
                state = "REVIEW_REQUIRED_AGGREGATE" if destination["aggregate"] else "REVIEW_REQUIRED"
                reason = "exact normalized name equality; identity provenance still requires human review"
            else:
                continue
            matched_slugs.add(destination["slug"])
            candidates.append({
                "destination_slug": destination["slug"], "destination_name_ar": destination["name_ar"],
                "destination_name_en": destination["name_en"], "source_id": feature.source_id,
                "source_file": specs[feature.source_id].expected_filename, "source_feature_id": feature.feature_id,
                "source_name": feature.raw_name, "latitude": feature.latitude, "longitude": feature.longitude,
                "match_reason": reason, "review_status": state, "source_reference": feature.source_reference,
            })
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["destination_slug"]].append(candidate)
    aggregate_lookup = {item["slug"]: item["aggregate"] for item in canonical}
    for slug, group in grouped.items():
        non_id = [item for item in group if item["review_status"] != "EXACT_ID"]
        if len(non_id) > 1 and not aggregate_lookup[slug]:
            for item in non_id:
                item["review_status"] = "AMBIGUOUS"
                item["match_reason"] += "; multiple exact-name source candidates exist"
    unresolved = {item["slug"]: "NO_MATCH" for item in canonical if item["slug"] not in matched_slugs}
    return sorted(candidates, key=lambda item: (item["destination_slug"], item["source_id"], item["source_feature_id"])), unresolved


def natural_relationship(base: list[NormalizedFeature] | None, media: list[NormalizedFeature] | None) -> dict[str, Any]:
    if base is None or media is None:
        return {"status": "UNRESOLVED_MISSING_SOURCE", "identity_basis": None}
    base_native = {item.source_feature_id for item in base if item.source_feature_id}
    media_native = {item.source_feature_id for item in media if item.source_feature_id}
    if len(base_native) == len(base) and len(media_native) == len(media) and base_native == media_native:
        return {"status": "PROVEN_SAME_NATIVE_IDS", "identity_basis": "native feature IDs", "shared_features": len(base_native)}
    return {"status": "UNRESOLVED_IDENTITY", "identity_basis": None, "base_features": len(base), "media_features": len(media)}


def taxonomy_crosswalk(features: list[NormalizedFeature], canonical: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    source_categories = Counter(item.category for item in features if item.category)
    destination_categories = {item["category"] for item in canonical}
    output = []
    for category, count in sorted(source_categories.items()):
        normalized = normalize_name(category).replace(" ", "-")
        if normalized in destination_categories:
            target, status = normalized, "EXACT"
        else:
            target, status = None, "REVIEW_REQUIRED"
        output.append({"source_category": category, "feature_count": count, "visit_libya_category": target, "mapping_status": status})
    return output


def source_registry_entry(spec: SourceSpec, audit: SourceAudit, organization: str) -> dict[str, Any]:
    return {
        "source_id": spec.source_id, "source_type": "institutional_gis", "title": spec.title,
        "organization": organization, "file_name": spec.expected_filename, "format": spec.format,
        "dataset_role": spec.dataset_role, "source_scope": spec.source_scope,
        "status": audit.parse_status, "sha256": audit.sha256, "feature_count": audit.feature_count,
        "record_count": audit.record_count, "geometry_types": audit.geometry_types,
        "coordinate_system": "EPSG:4326" if spec.format == "geojson" else ("KML longitude/latitude (WGS84)" if spec.format == "kml" else None),
    }


def audit_sources(manifest: SourceManifest, source_dir: Path) -> tuple[dict[str, list[NormalizedFeature]], list[SourceAudit]]:
    feature_sets: dict[str, list[NormalizedFeature]] = {}; audits: list[SourceAudit] = []
    for spec in manifest.sources:
        path = safe_source_path(source_dir, spec.expected_filename)
        if not path.exists():
            audits.append(SourceAudit(spec.source_id, spec.expected_filename, spec.format, "missing", warnings=["expected source file was not supplied at the selected source directory"]))
            continue
        try:
            if spec.format == "kml":
                features, audit = parse_kml(spec, path)
            elif spec.format == "geojson":
                features, audit = parse_geojson(spec, path)
            else:
                features, audit = parse_json_registry(spec, path)
            feature_sets[spec.source_id] = features; audits.append(audit)
        except Exception as exc:
            try:
                raw, digest = _read_source(path)
                audits.append(SourceAudit(
                    spec.source_id, spec.expected_filename, spec.format, "malformed",
                    sha256=digest, size_bytes=len(raw), encoding="UTF-8", warnings=[str(exc)],
                ))
            except Exception as read_exc:
                audits.append(SourceAudit(spec.source_id, spec.expected_filename, spec.format, "malformed", warnings=[str(read_exc)]))
    return feature_sets, audits


def serialize_features(features: list[NormalizedFeature]) -> list[dict[str, Any]]:
    return [asdict(item) for item in features]
