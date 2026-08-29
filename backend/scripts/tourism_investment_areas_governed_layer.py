#!/usr/bin/env python3
"""Build governed review artifacts for tourism development/investment areas.

The institutional Excel workbook is the identity/attribute authority. Only the
GDB layer ``مناطق_التنمية_والاستثمار_السياحي_1`` supplies geometry. The older
mixed investment KML and the GDB projects layer are deliberately excluded.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"
ATLAS = ROOT / "atlas"
WORKBOOK = ATLAS / "مناطق تنمية والاستثمار.xlsx"
GDB_REVIEW = GIS / "tourism-investment-gdb-source.review.geojson"
SOURCE = GIS / "tourism-investment-areas-source.review.geojson"
RECONCILIATION = GIS / "tourism-investment-areas-reconciliation.review.json"
IMPORT = GIS / "tourism-investment-areas-governed-import.review.geojson"
BLOCKED = GIS / "tourism-investment-areas-governed-blocked.review.json"
CROSS = GIS / "tourism-investment-areas-cross-layer-review.json"

LAYER_CODE = "TOURISM_INVESTMENT"
SEMANTIC_LAYER_CODE = "TOURISM_DEVELOPMENT_INVESTMENT_AREAS"
SEMANTIC_NAME_AR = "مناطق التنمية والاستثمار السياحي"
SEMANTIC_NAME_EN = "Tourism Development and Investment Areas"
GDB_AREA_LAYER = "مناطق_التنمية_والاستثمار_السياحي_1"
DEPRECATED_GDB_LAYER = "المشاريع_السياحية_الاستثمارية"
WORKBOOK_SHA256 = "fc8e4cbc32cce2ac81a3cce19374bc49cf092790379692990705f8d7085750fd"
STATUS = "GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL"

EXPECTED_COLUMNS = [
    "المجلد",
    "الاسم",
    "FID",
    "المساحة (هكتار)",
    "محيط الشكل (Shape_Length)",
    "الوصف",
    "X (خط الطول - Longitude)",
    "Y (خط العرض - Latitude)",
    "المساحة المحسوبة (كم2)",
    "عدد نقاط الحدود",
]


class TourismInvestmentAreasError(ValueError):
    pass


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[ـًٌٍَُِّْ]", "", text)
    text = text.translate(str.maketrans("أإآٱى", "ااااي"))
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def valid_point(geometry: object) -> bool:
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return False
    try:
        x, y = (float(v) for v in geometry["coordinates"][:2])
    except (KeyError, TypeError, ValueError):
        return False
    return math.isfinite(x) and math.isfinite(y) and -180 <= x <= 180 and -90 <= y <= 90


def point_key(geometry: dict) -> tuple[float, float]:
    return tuple(round(float(v), 7) for v in geometry["coordinates"][:2])


def distance_km(left: tuple[float, float], right: tuple[float, float]) -> float:
    mean_lat = math.radians((left[1] + right[1]) / 2)
    dx = (left[0] - right[0]) * math.cos(mean_lat)
    dy = left[1] - right[1]
    return round(111.32 * math.hypot(dx, dy), 6)


def _column_letters(reference: str) -> str:
    match = re.match(r"[A-Z]+", reference)
    if not match:
        raise TourismInvestmentAreasError(f"Invalid XLSX cell reference: {reference}")
    return match.group()


def read_workbook_rows() -> tuple[list[str], list[dict]]:
    """Read the source XLSX without modifying it or adding a runtime dependency."""
    if sha256(WORKBOOK) != WORKBOOK_SHA256:
        raise TourismInvestmentAreasError("Institutional investment-areas workbook hash mismatch")
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    ns = {"m": main_ns, "r": rel_ns}
    with zipfile.ZipFile(WORKBOOK) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("m:si", ns):
                shared.append("".join(node.text or "" for node in item.iter(f"{{{main_ns}}}t")))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets = workbook.find("m:sheets", ns)
        if sheets is None:
            raise TourismInvestmentAreasError("Workbook has no sheets")
        sheet_items = list(sheets)
        sheet_names = [item.attrib["name"] for item in sheet_items]
        if sheet_names != ["Sheet1"]:
            raise TourismInvestmentAreasError(f"Unexpected workbook sheets: {sheet_names}")
        target = targets[sheet_items[0].attrib[f"{{{rel_ns}}}id"]].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheet = ET.fromstring(archive.read(target))
        raw_rows: list[dict[str, object]] = []
        for row in sheet.findall(".//m:sheetData/m:row", ns):
            values: dict[str, object] = {}
            for cell in row.findall("m:c", ns):
                column = _column_letters(cell.attrib["r"])
                value_node = cell.find("m:v", ns)
                inline_node = cell.find("m:is", ns)
                cell_type = cell.attrib.get("t")
                value: object = None
                if cell_type == "s" and value_node is not None:
                    value = shared[int(value_node.text or 0)]
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(
                        node.text or "" for node in inline_node.iter(f"{{{main_ns}}}t")
                    )
                elif value_node is not None:
                    value = value_node.text
                values[column] = value
            raw_rows.append({"xlsx_row_number": int(row.attrib["r"]), "values": values})
    if not raw_rows:
        raise TourismInvestmentAreasError("Workbook is empty")
    headers = [raw_rows[0]["values"].get(chr(ord("A") + index)) for index in range(10)]
    if headers != EXPECTED_COLUMNS:
        raise TourismInvestmentAreasError(f"Unexpected workbook columns: {headers}")
    records: list[dict] = []
    for row in raw_rows[1:]:
        values = row["values"]
        records.append(
            {
                "xlsx_row_number": row["xlsx_row_number"],
                "attributes": {
                    header: values.get(chr(ord("A") + index))
                    for index, header in enumerate(EXPECTED_COLUMNS)
                },
            }
        )
    if len(records) != 141:
        raise TourismInvestmentAreasError(f"Expected 141 Excel records, found {len(records)}")
    return sheet_names, records


def build_source() -> dict:
    sheet_names, excel_records = read_workbook_rows()
    legacy = load(GDB_REVIEW)
    all_gdb = legacy.get("features", [])
    areas = [
        feature
        for feature in all_gdb
        if feature.get("properties", {}).get("source_layer") == GDB_AREA_LAYER
    ]
    excluded = [
        feature
        for feature in all_gdb
        if feature.get("properties", {}).get("source_layer") == DEPRECATED_GDB_LAYER
    ]
    if len(areas) != 36 or len(excluded) != 10:
        raise TourismInvestmentAreasError("Unexpected filtered GDB layer accounting")
    if any(feature.get("geometry", {}).get("type") != "Point" for feature in areas):
        raise TourismInvestmentAreasError("Unexpected GDB investment-area geometry type")

    features: list[dict] = []
    for record in excel_records:
        row_number = record["xlsx_row_number"]
        attributes = record["attributes"]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "source_id": "INSTITUTIONAL_INVESTMENT_AREAS_XLSX_2026",
                    "source_database": WORKBOOK.name,
                    "source_filename": WORKBOOK.name,
                    "source_layer": "Sheet1",
                    "source_subtype": "tourism_development_investment_area_attribute_record",
                    "source_feature_id": f"Sheet1:row-{row_number}",
                    "source_composite_id": f"{WORKBOOK.name}:Sheet1:row-{row_number}",
                    "source_attributes": attributes,
                    "target_layer": LAYER_CODE,
                    "semantic_layer_code": SEMANTIC_LAYER_CODE,
                    "governance_role": "INSTITUTIONAL_IDENTITY_ATTRIBUTE_AUTHORITY",
                    "authority_status": "UNAPPROVED",
                    "review_status": "REVIEW_REQUIRED",
                    "publication_approved": False,
                    "canonical_identity_approved": False,
                    "authoritative_boundary_claimed": False,
                    "is_published": False,
                },
                "geometry": None,
            }
        )
    for original in areas:
        feature = json.loads(json.dumps(original, ensure_ascii=False))
        properties = feature["properties"]
        properties.update(
            {
                "source_subtype": "tourism_development_investment_area_reference_point",
                "semantic_layer_code": SEMANTIC_LAYER_CODE,
                "governance_role": "INSTITUTIONAL_GDB_GEOMETRY_AUTHORITY",
                "authority_status": "UNAPPROVED",
                "review_status": "REVIEW_REQUIRED",
                "publication_approved": False,
                "canonical_identity_approved": False,
                "authoritative_boundary_claimed": False,
                "is_published": False,
            }
        )
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "schema_version": 1,
        "artifact_status": "SOURCE_REVIEW_ONLY_NOT_PUBLICATION_APPROVAL",
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "semantic_name_ar": SEMANTIC_NAME_AR,
        "semantic_name_en": SEMANTIC_NAME_EN,
        "source_feature_count": 177,
        "excel_record_count": 141,
        "gdb_area_record_count": 36,
        "excluded_deprecated_gdb_project_count": 10,
        "workbook_sheet_names": sheet_names,
        "workbook_columns": EXPECTED_COLUMNS,
        "workbook_sha256": WORKBOOK_SHA256,
        "gdb_source_layer": GDB_AREA_LAYER,
        "deprecated_sources_excluded": [
            DEPRECATED_GDB_LAYER,
            "المشاريع وفرص الاستثمار السياحي KML (mixed projects/areas)",
        ],
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "features": features,
    }


def _excel_records(source: dict) -> list[dict]:
    return [
        feature
        for feature in source["features"]
        if feature["properties"].get("source_id")
        == "INSTITUTIONAL_INVESTMENT_AREAS_XLSX_2026"
    ]


def _gdb_records(source: dict) -> list[dict]:
    return [
        feature
        for feature in source["features"]
        if feature["properties"].get("source_layer") == GDB_AREA_LAYER
    ]


def _excel_coordinate(feature: dict) -> tuple[float, float] | None:
    attributes = feature["properties"]["source_attributes"]
    try:
        coordinate = (
            float(attributes["X (خط الطول - Longitude)"]),
            float(attributes["Y (خط العرض - Latitude)"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in coordinate):
        return None
    return coordinate


def _record_reference(feature: dict) -> dict:
    properties = feature["properties"]
    return {
        "source_id": properties.get("source_id"),
        "source_database": properties.get("source_database"),
        "source_layer": properties.get("source_layer"),
        "source_feature_id": properties.get("source_feature_id"),
        "source_composite_id": properties.get("source_composite_id"),
    }


def reconcile(source: dict) -> dict:
    if source.get("source_feature_count") != 177 or len(source.get("features", [])) != 177:
        raise TourismInvestmentAreasError("Investment-area source accounting failed")
    excel = _excel_records(source)
    gdb = _gdb_records(source)
    if len(excel) != 141 or len(gdb) != 36:
        raise TourismInvestmentAreasError("Excel/GDB filtered source accounting failed")

    excel_by_name: dict[str, list[int]] = defaultdict(list)
    gdb_by_name: dict[str, list[int]] = defaultdict(list)
    for index, feature in enumerate(excel):
        excel_by_name[normalize_name(feature["properties"]["source_attributes"].get("الاسم"))].append(index)
    for index, feature in enumerate(gdb):
        gdb_by_name[normalize_name(feature["properties"]["source_attributes"].get("الاسم"))].append(index)

    matches: list[dict] = []
    matched_excel: set[int] = set()
    matched_gdb: set[int] = set()
    for normalized_name in sorted(set(excel_by_name) & set(gdb_by_name)):
        if not normalized_name:
            continue
        excel_indexes = excel_by_name[normalized_name]
        gdb_indexes = gdb_by_name[normalized_name]
        if len(excel_indexes) != 1 or len(gdb_indexes) != 1:
            continue
        excel_index, gdb_index = excel_indexes[0], gdb_indexes[0]
        excel_feature, gdb_feature = excel[excel_index], gdb[gdb_index]
        excel_coord = _excel_coordinate(excel_feature)
        gdb_coord = tuple(float(value) for value in gdb_feature["geometry"]["coordinates"][:2])
        matches.append(
            {
                "match_id": f"excel-{excel_feature['properties']['source_feature_id']}__gdb-{gdb_feature['properties']['source_feature_id']}",
                "match_method": "NORMALIZED_EXACT_AREA_NAME",
                "normalized_area_name": normalized_name,
                "excel": _record_reference(excel_feature),
                "gdb": _record_reference(gdb_feature),
                "excel_representative_coordinate": list(excel_coord) if excel_coord else None,
                "gdb_reference_geometry_coordinate": list(gdb_coord),
                "coordinate_distance_km": distance_km(excel_coord, gdb_coord) if excel_coord else None,
                "coordinate_role": "CORROBORATING_EVIDENCE_ONLY_NOT_BOUNDARY",
                "fid_match_used": False,
                "fid_compatibility": "INCOMPATIBLE_SOURCE_NAMESPACES",
            }
        )
        matched_excel.add(excel_index)
        matched_gdb.add(gdb_index)

    excel_only = []
    for index, feature in enumerate(excel):
        if index in matched_excel:
            continue
        excel_only.append(
            {
                **_record_reference(feature),
                "area_name": feature["properties"]["source_attributes"].get("الاسم"),
                "normalized_area_name": normalize_name(feature["properties"]["source_attributes"].get("الاسم")),
                "representative_coordinate": list(_excel_coordinate(feature)) if _excel_coordinate(feature) else None,
                "review_reason": "NO_NORMALIZED_EXACT_GDB_IDENTITY_MATCH",
                "geometry_status": "NO_AUTHORITATIVE_GDB_GEOMETRY_MATCH",
            }
        )
    gdb_only = []
    for index, feature in enumerate(gdb):
        if index in matched_gdb:
            continue
        coordinate = tuple(float(value) for value in feature["geometry"]["coordinates"][:2])
        nearest = sorted(
            (
                distance_km(coordinate, excel_coordinate),
                excel_feature,
            )
            for excel_feature in excel
            if (excel_coordinate := _excel_coordinate(excel_feature)) is not None
        )[0]
        gdb_only.append(
            {
                **_record_reference(feature),
                "area_name": feature["properties"]["source_attributes"].get("الاسم"),
                "normalized_area_name": normalize_name(feature["properties"]["source_attributes"].get("الاسم")),
                "geometry": feature["geometry"],
                "review_reason": "NO_NORMALIZED_EXACT_EXCEL_IDENTITY_MATCH",
                "nearest_excel_coordinate_candidate": {
                    "source_feature_id": nearest[1]["properties"]["source_feature_id"],
                    "area_name": nearest[1]["properties"]["source_attributes"].get("الاسم"),
                    "distance_km": nearest[0],
                    "match_created": False,
                },
            }
        )

    name_counts = Counter(
        normalize_name(feature["properties"]["source_attributes"].get("الاسم"))
        for feature in excel
        if normalize_name(feature["properties"]["source_attributes"].get("الاسم"))
    )
    fid_values = [
        feature["properties"]["source_attributes"].get("FID")
        for feature in excel
        if feature["properties"]["source_attributes"].get("FID") not in (None, "")
    ]
    coordinate_coverage = sum(_excel_coordinate(feature) is not None for feature in excel)
    area_ha_coverage = sum(
        feature["properties"]["source_attributes"].get("المساحة (هكتار)") not in (None, "")
        for feature in excel
    )
    area_km2_coverage = sum(
        feature["properties"]["source_attributes"].get("المساحة المحسوبة (كم2)") not in (None, "")
        for feature in excel
    )
    area_inconsistencies = []
    for feature in excel:
        attributes = feature["properties"]["source_attributes"]
        try:
            hectares = float(attributes["المساحة (هكتار)"])
            square_km = float(attributes["المساحة المحسوبة (كم2)"])
        except (KeyError, TypeError, ValueError):
            continue
        delta = square_km - hectares / 100
        if abs(delta) > max(0.01, abs(hectares / 100) * 0.01):
            area_inconsistencies.append(
                {
                    "source_feature_id": feature["properties"]["source_feature_id"],
                    "area_name": attributes.get("الاسم"),
                    "source_hectares": hectares,
                    "source_calculated_square_kilometres": square_km,
                    "difference_square_kilometres": round(delta, 12),
                    "source_values_repaired": False,
                }
            )

    return {
        "schema_version": 1,
        "inventory_id": "tourism-investment-areas-reconciliation-v1",
        "artifact_status": STATUS,
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "matching_policy": {
            "fid": "NOT_USED_INCOMPATIBLE_SOURCE_NAMESPACES",
            "identity": "NORMALIZED_EXACT_AREA_NAME_ONLY",
            "coordinates": "CORROBORATING_EVIDENCE_ONLY_NOT_A_MATCH_KEY_OR_BOUNDARY",
            "area_values": "CORROBORATING_EVIDENCE_ONLY_NOT_A_MATCH_KEY",
            "approximate_name_matching": False,
        },
        "excel_record_count": len(excel),
        "gdb_area_record_count": len(gdb),
        "matched_count": len(matches),
        "excel_only_count": len(excel_only),
        "gdb_only_count": len(gdb_only),
        "reconciled_candidate_count": len(matches) + len(excel_only) + len(gdb_only),
        "workbook_quality": {
            "sheet_names": source["workbook_sheet_names"],
            "column_names": source["workbook_columns"],
            "unique_area_name_count": len(name_counts),
            "missing_name_count": sum(
                not normalize_name(feature["properties"]["source_attributes"].get("الاسم"))
                for feature in excel
            ),
            "duplicate_name_group_count": sum(count > 1 for count in name_counts.values()),
            "duplicate_name_record_count": sum(count for count in name_counts.values() if count > 1),
            "fid_coverage_count": len(fid_values),
            "fid_missing_count": len(excel) - len(fid_values),
            "fid_unique_count": len(set(fid_values)),
            "xy_coverage_count": coordinate_coverage,
            "area_hectare_coverage_count": area_ha_coverage,
            "calculated_square_kilometre_coverage_count": area_km2_coverage,
            "boundary_point_count_metadata_coverage_count": sum(
                feature["properties"]["source_attributes"].get("عدد نقاط الحدود") not in (None, "")
                for feature in excel
            ),
            "shape_length_metadata_coverage_count": sum(
                feature["properties"]["source_attributes"].get("محيط الشكل (Shape_Length)") not in (None, "")
                for feature in excel
            ),
            "area_value_inconsistency_count": len(area_inconsistencies),
            "area_value_inconsistencies": area_inconsistencies,
            "source_values_repaired": False,
        },
        "gdb_geometry_inventory": {
            "Point": len(gdb),
            "Polygon": 0,
            "authoritative_boundary_claimed_count": 0,
            "valid_wgs84_reference_point_count": sum(valid_point(feature.get("geometry")) for feature in gdb),
        },
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "matches": matches,
        "excel_only": excel_only,
        "gdb_only": gdb_only,
    }


def comparison_points() -> dict[tuple[float, float], list[dict]]:
    index: dict[tuple[float, float], list[dict]] = defaultdict(list)
    paths = {
        "HOTELS": GIS / "hotels-governed-import.review.geojson",
        "TOURISM_RESORTS": GIS / "tourism-resorts-governed-import.review.geojson",
        "PARKS": GIS / "parks-governed-import.review.geojson",
    }
    for layer_code, path in paths.items():
        if not path.is_file():
            continue
        for feature in load(path).get("features", []):
            geometry = feature.get("geometry")
            if valid_point(geometry):
                properties = feature.get("properties", {})
                index[point_key(geometry)].append(
                    {
                        "layer_code": layer_code,
                        "institutional_id": properties.get("institutional_id"),
                        "source_feature_id": properties.get("source_feature_id"),
                        "name_ar": properties.get("name_ar"),
                    }
                )
    return index


def build_governed(source: dict) -> tuple[dict, dict, dict, dict]:
    reconciliation = reconcile(source)
    excel_by_id = {
        feature["properties"]["source_feature_id"]: feature
        for feature in _excel_records(source)
    }
    gdb_by_id = {
        feature["properties"]["source_feature_id"]: feature
        for feature in _gdb_records(source)
    }
    gdb_coordinate_names: dict[tuple[float, float], set[str]] = defaultdict(set)
    for feature in gdb_by_id.values():
        if valid_point(feature.get("geometry")):
            gdb_coordinate_names[point_key(feature["geometry"])].add(
                normalize_name(feature["properties"]["source_attributes"].get("الاسم"))
            )
    external_points = comparison_points()
    safe: list[dict] = []
    blocked: list[dict] = []
    cross_records: list[dict] = []

    for match in reconciliation["matches"]:
        excel_feature = excel_by_id[match["excel"]["source_feature_id"]]
        gdb_feature = gdb_by_id[match["gdb"]["source_feature_id"]]
        excel_attributes = excel_feature["properties"]["source_attributes"]
        gdb_attributes = gdb_feature["properties"]["source_attributes"]
        name = excel_attributes.get("الاسم")
        geometry = gdb_feature.get("geometry")
        key = point_key(geometry) if valid_point(geometry) else None
        classification = "SAFE_INVESTMENT_AREA_REFERENCE_POINT"
        if not normalize_name(name):
            classification = "MISSING_IDENTITY_REVIEW"
        elif not valid_point(geometry):
            classification = "SOURCE_GEOMETRY_CRS_REVIEW"
        elif len(gdb_coordinate_names[key]) > 1:
            classification = "SAME_GEOMETRY_DIFFERENT_IDENTITY_REVIEW"
        identity_seed = f"{excel_feature['properties']['source_composite_id']}|{gdb_feature['properties']['source_composite_id']}"
        institutional_id = "atlas-investment-area-" + hashlib.sha256(
            identity_seed.encode("utf-8")
        ).hexdigest()[:20]
        source_metadata = {
            "artifact_status": STATUS,
            "semantic_layer_code": SEMANTIC_LAYER_CODE,
            "semantic_name_ar": SEMANTIC_NAME_AR,
            "semantic_name_en": SEMANTIC_NAME_EN,
            "review_classification": classification,
            "match_method": match["match_method"],
            "excel_source": _record_reference(excel_feature),
            "excel_source_attributes": excel_attributes,
            "gdb_source": _record_reference(gdb_feature),
            "gdb_source_attributes": gdb_attributes,
            "excel_representative_coordinate": match["excel_representative_coordinate"],
            "coordinate_distance_km": match["coordinate_distance_km"],
            "coordinate_role": "REPRESENTATIVE_REFERENCE_ONLY_NOT_BOUNDARY",
            "source_geometry_role": "GDB_REFERENCE_POINT_NOT_AREA_BOUNDARY",
            "publication_approved": False,
            "canonical_identity_approved": False,
            "authoritative_boundary_claimed": False,
        }
        if classification == "SAFE_INVESTMENT_AREA_REFERENCE_POINT":
            safe.append(
                {
                    "type": "Feature",
                    "properties": {
                        "feature_code": institutional_id,
                        "institutional_id": institutional_id,
                        "source_feature_id": gdb_feature["properties"]["source_feature_id"],
                        "name_ar": name,
                        "name_en": None,
                        "category": "tourism_investment",
                        "semantic_layer_code": SEMANTIC_LAYER_CODE,
                        "review_classification": classification,
                        "area_hectares_source": excel_attributes.get("المساحة (هكتار)"),
                        "calculated_square_kilometres_source": excel_attributes.get("المساحة المحسوبة (كم2)"),
                        "source_identity": identity_seed,
                        "source_metadata": source_metadata,
                    },
                    "geometry": geometry,
                }
            )
        else:
            blocked.append(
                {
                    "institutional_id": institutional_id,
                    "area_name": name,
                    "review_classification": classification,
                    "blocked_reason": classification,
                    "geometry": geometry,
                    "source_metadata": source_metadata,
                }
            )
        if key and external_points.get(key):
            cross_records.append(
                {
                    "investment_area_institutional_id": institutional_id,
                    "investment_area_name_ar": name,
                    "coordinate": list(key),
                    "relationship": "CROSS_LAYER_REFERENCE",
                    "relationship_reason": "EXACT_SOURCE_POINT_COORDINATE_ONLY_NO_CONTAINMENT_INFERRED",
                    "matches": external_points[key],
                    "publication_approved": False,
                }
            )

    for record in reconciliation["excel_only"]:
        feature = excel_by_id[record["source_feature_id"]]
        attributes = feature["properties"]["source_attributes"]
        classification = (
            "MISSING_IDENTITY_REVIEW"
            if not normalize_name(attributes.get("الاسم"))
            else "EXCEL_ONLY_NO_AUTHORITATIVE_GDB_GEOMETRY_REVIEW"
        )
        blocked.append(
            {
                "area_name": attributes.get("الاسم"),
                "review_classification": classification,
                "blocked_reason": classification,
                "geometry": None,
                "representative_coordinate": record["representative_coordinate"],
                "representative_coordinate_boundary_claimed": False,
                "source_metadata": {
                    "artifact_status": STATUS,
                    "semantic_layer_code": SEMANTIC_LAYER_CODE,
                    "excel_source": _record_reference(feature),
                    "excel_source_attributes": attributes,
                    "publication_approved": False,
                    "canonical_identity_approved": False,
                    "authoritative_boundary_claimed": False,
                },
            }
        )
    for record in reconciliation["gdb_only"]:
        feature = gdb_by_id[record["source_feature_id"]]
        blocked.append(
            {
                "area_name": record["area_name"],
                "review_classification": "GDB_ONLY_IDENTITY_RECONCILIATION_REVIEW",
                "blocked_reason": "GDB_ONLY_IDENTITY_RECONCILIATION_REVIEW",
                "geometry": feature["geometry"],
                "nearest_excel_coordinate_candidate": record["nearest_excel_coordinate_candidate"],
                "source_metadata": {
                    "artifact_status": STATUS,
                    "semantic_layer_code": SEMANTIC_LAYER_CODE,
                    "gdb_source": _record_reference(feature),
                    "gdb_source_attributes": feature["properties"]["source_attributes"],
                    "publication_approved": False,
                    "canonical_identity_approved": False,
                    "authoritative_boundary_claimed": False,
                },
            }
        )

    classifications = Counter(item["review_classification"] for item in blocked)
    classifications["SAFE_INVESTMENT_AREA_REFERENCE_POINT"] = len(safe)
    common = {
        "artifact_status": STATUS,
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "semantic_name_ar": SEMANTIC_NAME_AR,
        "semantic_name_en": SEMANTIC_NAME_EN,
        "excel_record_count": 141,
        "gdb_area_record_count": 36,
        "matched_count": reconciliation["matched_count"],
        "excel_only_count": reconciliation["excel_only_count"],
        "gdb_only_count": reconciliation["gdb_only_count"],
        "safe_ingestible_feature_count": len(safe),
        "blocked_feature_count": len(blocked),
        "classification_counts": dict(sorted(classifications.items())),
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
    }
    governed_import = {
        "type": "FeatureCollection",
        "name": "TOURISM DEVELOPMENT AND INVESTMENT AREAS governed review import",
        **common,
        "features": safe,
    }
    governed_blocked = {
        "schema_version": 1,
        "inventory_id": "tourism-investment-areas-governed-blocked-v1",
        **common,
        "records": blocked,
    }
    cross_layer = {
        "schema_version": 1,
        "inventory_id": "tourism-investment-areas-cross-layer-review-v1",
        "artifact_status": STATUS,
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "comparison_layers": ["HOTELS", "TOURISM_RESORTS", "PARKS"],
        "cross_layer_reference_count": len(cross_records),
        "polygon_containment_relationship_count": 0,
        "polygon_containment_reason": "SOURCE_GDB_AREA_LAYER_CONTAINS_POINTS_ONLY",
        "publication_approved": False,
        "canonical_identity_approved": False,
        "authoritative_boundary_claimed": False,
        "records": cross_records,
    }
    return reconciliation, governed_import, governed_blocked, cross_layer


def validate() -> tuple[dict, dict, dict, dict, dict]:
    if not SOURCE.is_file():
        raise TourismInvestmentAreasError(f"Missing source artifact: {SOURCE.name}")
    source = load(SOURCE)
    if source.get("workbook_sha256") != WORKBOOK_SHA256:
        raise TourismInvestmentAreasError("Committed source workbook identity mismatch")
    built = build_governed(source)
    for path, artifact in zip((RECONCILIATION, IMPORT, BLOCKED, CROSS), built):
        if not path.is_file() or path.read_bytes() != canonical_bytes(artifact):
            raise TourismInvestmentAreasError(f"Artifact missing or stale: {path.name}")
    reconciliation, governed_import, governed_blocked, cross_layer = built
    if reconciliation["matched_count"] + reconciliation["excel_only_count"] != 141:
        raise TourismInvestmentAreasError("Excel reconciliation accounting failed")
    if reconciliation["matched_count"] + reconciliation["gdb_only_count"] != 36:
        raise TourismInvestmentAreasError("GDB reconciliation accounting failed")
    if len(governed_import["features"]) + len(governed_blocked["records"]) != 146:
        raise TourismInvestmentAreasError("Governed candidate accounting failed")
    return source, reconciliation, governed_import, governed_blocked, cross_layer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        source = build_source()
        SOURCE.write_bytes(canonical_bytes(source))
        for path, artifact in zip(
            (RECONCILIATION, IMPORT, BLOCKED, CROSS), build_governed(source)
        ):
            path.write_bytes(canonical_bytes(artifact))
    _, reconciliation, governed_import, governed_blocked, cross_layer = validate()
    print("TOURISM INVESTMENT AREAS GOVERNED REVIEW ARTIFACTS VALID")
    print("EXCEL RECORDS:", reconciliation["excel_record_count"])
    print("GDB AREA RECORDS:", reconciliation["gdb_area_record_count"])
    print("MATCHED:", reconciliation["matched_count"])
    print("EXCEL ONLY:", reconciliation["excel_only_count"])
    print("GDB ONLY:", reconciliation["gdb_only_count"])
    print("SAFE:", len(governed_import["features"]))
    print("BLOCKED:", len(governed_blocked["records"]))
    print("CROSS LAYER REFERENCES:", len(cross_layer["records"]))
    print("COUNTS:", json.dumps(governed_import["classification_counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
