#!/usr/bin/env python3
"""Build the authoritative 141-area tourism-investment governed dataset."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from shapely import make_valid, to_wkt
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.validation import explain_validity


ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / "backend/data/gis"
ATLAS = ROOT / "atlas"
EXCEL = ATLAS / "مناطق تنمية والاستثمار-معتمد-وادي الخبطة.xlsx"
KML = ATLAS / "مناطق_التنمية_والاستثمار_السياحي-معتمد-وادي_الخبطة.kml"
SOURCE = GIS / "tourism-investment-areas-authoritative-source.review.geojson"
RECONCILIATION = GIS / "tourism-investment-areas-authoritative-reconciliation.json"
IMPORT = GIS / "tourism-investment-areas-governed-import.geojson"
CROSS = GIS / "tourism-investment-areas-authoritative-cross-layer-review.json"

LAYER_CODE = "TOURISM_INVESTMENT"
SEMANTIC_LAYER_CODE = "TOURISM_DEVELOPMENT_INVESTMENT_AREAS"
SEMANTIC_NAME_AR = "مناطق التنمية والاستثمار السياحي"
SEMANTIC_NAME_EN = "Tourism Development and Investment Areas"
EXCEL_SHA256 = "d69c97303732082a5e51fdbc563137793decbc532b62be8bd39cb7d89f5bdfbd"
KML_SHA256 = "dcc0d94c98e3f42ae9e2939e3156be02aed03ae2e851a2730f3e1d76d50a7bfa"
APPROVAL_BASIS = "INSTITUTIONAL_DATA_OWNER_CONFIRMED_141_OFFICIAL_AREAS"
REPAIR_BASIS = "INSTITUTIONAL_SOURCE_TOPOLOGY_CORRECTION"
EXPECTED_COLUMNS = [
    "المجلد", "الاسم", "FID", "المساحة (هكتار)",
    "محيط الشكل (Shape_Length)", "الوصف",
    "X (خط الطول - Longitude)", "Y (خط العرض - Latitude)",
    "المساحة المحسوبة (كم2)", "عدد نقاط الحدود",
]


class AuthoritativeInvestmentAreasError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[ـًٌٍَُِّْ]", "", text)
    text = text.translate(str.maketrans("أإآٱى", "ااااي"))
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def geometry_hash(geometry: dict) -> str:
    payload = json.dumps(geometry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def geojson_mapping(geometry) -> dict:
    """Return a JSON-native mapping (lists, never Shapely coordinate tuples)."""
    return json.loads(json.dumps(mapping(geometry), ensure_ascii=True))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _read_excel() -> tuple[list[str], list[dict]]:
    if file_sha256(EXCEL) != EXCEL_SHA256:
        raise AuthoritativeInvestmentAreasError("Corrected Excel SHA-256 mismatch")
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    ns = {"m": main_ns, "r": rel_ns}
    with zipfile.ZipFile(EXCEL) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter(f"{{{main_ns}}}t"))
                for item in root.findall("m:si", ns)
            ]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets_element = workbook.find("m:sheets", ns)
        sheets = list(sheets_element) if sheets_element is not None else []
        sheet_names = [item.attrib["name"] for item in sheets]
        if sheet_names != ["Sheet1"]:
            raise AuthoritativeInvestmentAreasError(f"Unexpected Excel sheets: {sheet_names}")
        target = targets[sheets[0].attrib[f"{{{rel_ns}}}id"]].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        worksheet = ET.fromstring(archive.read(target))
        raw_rows: list[tuple[int, dict[str, object]]] = []
        for row in worksheet.findall(".//m:sheetData/m:row", ns):
            values: dict[str, object] = {}
            for cell in row.findall("m:c", ns):
                match = re.match(r"[A-Z]+", cell.attrib["r"])
                if not match:
                    raise AuthoritativeInvestmentAreasError("Invalid Excel cell reference")
                column = match.group()
                value_node = cell.find("m:v", ns)
                inline_node = cell.find("m:is", ns)
                cell_type = cell.attrib.get("t")
                value: object = None
                if cell_type == "s" and value_node is not None:
                    value = shared[int(value_node.text or 0)]
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(node.text or "" for node in inline_node.iter(f"{{{main_ns}}}t"))
                elif value_node is not None:
                    value = value_node.text
                values[column] = value
            raw_rows.append((int(row.attrib["r"]), values))
    if not raw_rows:
        raise AuthoritativeInvestmentAreasError("Corrected Excel is empty")
    headers = [raw_rows[0][1].get(chr(ord("A") + index)) for index in range(10)]
    if headers != EXPECTED_COLUMNS:
        raise AuthoritativeInvestmentAreasError(f"Unexpected Excel columns: {headers}")
    records = []
    for row_number, values in raw_rows[1:]:
        records.append({
            "source_row_number": row_number,
            "attributes": {
                header: values.get(chr(ord("A") + index))
                for index, header in enumerate(EXPECTED_COLUMNS)
            },
        })
    if len(records) != 141:
        raise AuthoritativeInvestmentAreasError(f"Expected 141 Excel records, found {len(records)}")
    return sheet_names, records


def _coordinate_values(element: ET.Element) -> tuple[list[list[float]], str]:
    raw = _text(element) or ""
    coordinates = [[float(value) for value in token.split(",")] for token in raw.split()]
    return coordinates, raw


def _parse_polygon(element: ET.Element) -> tuple[list, list[str]]:
    rings: list[list[list[float]]] = []
    raw_coordinate_text: list[str] = []
    for boundary_name in ("outerBoundaryIs", "innerBoundaryIs"):
        for boundary in (item for item in element if _local_name(item.tag) == boundary_name):
            coordinate_element = next(
                (item for item in boundary.iter() if _local_name(item.tag) == "coordinates"),
                None,
            )
            if coordinate_element is None:
                raise AuthoritativeInvestmentAreasError("KML Polygon ring has no coordinates")
            coordinates, raw = _coordinate_values(coordinate_element)
            rings.append(coordinates)
            raw_coordinate_text.append(raw)
    if not rings:
        raise AuthoritativeInvestmentAreasError("KML Polygon has no rings")
    return rings, raw_coordinate_text


def _parse_kml() -> list[dict]:
    if file_sha256(KML) != KML_SHA256:
        raise AuthoritativeInvestmentAreasError("Corrected KML SHA-256 mismatch")
    root = ET.fromstring(KML.read_bytes())
    placemarks = [item for item in root.iter() if _local_name(item.tag) == "Placemark"]
    if len(placemarks) != 141:
        raise AuthoritativeInvestmentAreasError(f"Expected 141 KML Placemarks, found {len(placemarks)}")
    records = []
    for position, placemark in enumerate(placemarks, 1):
        name = _text(next((item for item in placemark if _local_name(item.tag) == "name"), None))
        description = _text(next((item for item in placemark if _local_name(item.tag) == "description"), None))
        fid_match = re.search(r"FID\s+(\d+)", re.sub(r"<[^>]+>", " ", description or ""))
        fid = int(fid_match.group(1)) if fid_match else None
        direct = [
            item for item in placemark
            if _local_name(item.tag) in {"Point", "Polygon", "MultiGeometry", "LineString"}
        ]
        if len(direct) != 1:
            raise AuthoritativeInvestmentAreasError(f"Placemark {position} has ambiguous geometry")
        source_type = _local_name(direct[0].tag)
        raw_text: list[str] = []
        if source_type == "Polygon":
            coordinates, text_values = _parse_polygon(direct[0])
            geometry = {"type": "Polygon", "coordinates": coordinates}
            raw_text.extend(text_values)
            polygon_member_count = 1
        elif source_type == "MultiGeometry":
            members = [item for item in direct[0] if _local_name(item.tag) in {"Polygon", "Point", "LineString", "MultiGeometry"}]
            if not members or any(_local_name(item.tag) != "Polygon" for item in members):
                raise AuthoritativeInvestmentAreasError(
                    f"Placemark {position} MultiGeometry is not polygon-only"
                )
            polygons = []
            for member in members:
                coordinates, text_values = _parse_polygon(member)
                polygons.append(coordinates)
                raw_text.extend(text_values)
            geometry = {"type": "MultiPolygon", "coordinates": polygons}
            polygon_member_count = len(polygons)
        else:
            raise AuthoritativeInvestmentAreasError(
                f"Unexpected investment-area KML geometry: {source_type}"
            )
        records.append({
            "source_order": position,
            "fid": fid,
            "name": name,
            "description": description,
            "source_geometry_type": source_type,
            "polygon_member_count": polygon_member_count,
            "raw_coordinate_text": raw_text,
            "geometry": geometry,
        })
    return records


def _stable_identity(fid: int | None, normalized_name: str) -> str:
    if fid is not None:
        return f"atlas-investment-area-fid-{fid:04d}"
    digest = hashlib.sha256(
        f"{SEMANTIC_LAYER_CODE}|{normalized_name}".encode("utf-8")
    ).hexdigest()[:20]
    return f"atlas-investment-area-name-{digest}"


def build_source() -> dict:
    sheet_names, excel_records = _read_excel()
    kml_records = _parse_kml()
    excel_by_fid: dict[int, dict] = {}
    kml_by_fid: dict[int, dict] = {}
    for record in excel_records:
        raw_fid = record["attributes"].get("FID")
        if raw_fid not in (None, ""):
            fid = int(float(raw_fid))
            if fid in excel_by_fid:
                raise AuthoritativeInvestmentAreasError(f"Duplicate Excel FID: {fid}")
            excel_by_fid[fid] = record
    for record in kml_records:
        if record["fid"] is not None:
            if record["fid"] in kml_by_fid:
                raise AuthoritativeInvestmentAreasError(f"Duplicate KML FID: {record['fid']}")
            kml_by_fid[record["fid"]] = record
    if set(excel_by_fid) != set(kml_by_fid):
        raise AuthoritativeInvestmentAreasError("Excel and KML FID sets differ")

    matched: list[tuple[dict, dict, str]] = []
    used_kml: set[int] = set()
    kml_by_name: dict[str, list[dict]] = {}
    for record in kml_records:
        kml_by_name.setdefault(normalize_name(record["name"]), []).append(record)
    for excel_record in excel_records:
        attributes = excel_record["attributes"]
        name_key = normalize_name(attributes.get("الاسم"))
        if not name_key:
            raise AuthoritativeInvestmentAreasError("Excel record has missing institutional name")
        raw_fid = attributes.get("FID")
        if raw_fid not in (None, ""):
            fid = int(float(raw_fid))
            kml_record = kml_by_fid[fid]
            method = "INSTITUTIONAL_FID"
            if normalize_name(kml_record["name"]) != name_key:
                raise AuthoritativeInvestmentAreasError(f"FID {fid} name conflict")
        else:
            candidates = [item for item in kml_by_name.get(name_key, []) if item["source_order"] not in used_kml]
            if len(candidates) != 1 or candidates[0]["fid"] is not None:
                raise AuthoritativeInvestmentAreasError(
                    f"No unique exact-name reconciliation for {attributes.get('الاسم')}"
                )
            kml_record = candidates[0]
            method = "NORMALIZED_EXACT_INSTITUTIONAL_NAME"
        if kml_record["source_order"] in used_kml:
            raise AuthoritativeInvestmentAreasError("KML record matched more than once")
        used_kml.add(kml_record["source_order"])
        matched.append((excel_record, kml_record, method))
    if len(matched) != 141 or len(used_kml) != 141:
        raise AuthoritativeInvestmentAreasError("141/141 reconciliation failed")

    features = []
    for excel_record, kml_record, method in matched:
        attributes = excel_record["attributes"]
        fid = int(float(attributes["FID"])) if attributes.get("FID") not in (None, "") else None
        normalized_name = normalize_name(attributes["الاسم"])
        institutional_id = _stable_identity(fid, normalized_name)
        raw_shape = shape(kml_record["geometry"])
        features.append({
            "type": "Feature",
            "properties": {
                "institutional_id": institutional_id,
                "fid": fid,
                "name_ar": attributes["الاسم"],
                "name_en": None,
                "source_feature_id": f"FID:{fid}" if fid is not None else f"NAME:{normalized_name}",
                "source_excel_identity": {
                    "source_filename": EXCEL.name,
                    "source_sheet": "Sheet1",
                    "source_row_number": excel_record["source_row_number"],
                    "sha256": EXCEL_SHA256,
                },
                "source_kml_identity": {
                    "source_filename": KML.name,
                    "placemark_position": kml_record["source_order"],
                    "placemark_name": kml_record["name"],
                    "sha256": KML_SHA256,
                },
                "source_attributes": attributes,
                "match_method": method,
                "source_geometry_type": kml_record["source_geometry_type"],
                "source_polygon_member_count": kml_record["polygon_member_count"],
                "source_geometry_geojson_sha256": geometry_hash(kml_record["geometry"]),
                "source_geometry_wkt_sha256": hashlib.sha256(
                    to_wkt(raw_shape, rounding_precision=-1).encode("utf-8")
                ).hexdigest(),
                "source_geometry_valid": raw_shape.is_valid,
                "source_geometry_validity_reason": explain_validity(raw_shape),
                "raw_kml_coordinate_text": kml_record["raw_coordinate_text"],
                "target_layer": LAYER_CODE,
                "semantic_layer_code": SEMANTIC_LAYER_CODE,
                "authority_status": "APPROVED",
                "review_status": "APPROVED",
                "canonical_identity_approved": True,
                "publication_approved": False,
                "is_published": False,
                "institutional_approval_basis": APPROVAL_BASIS,
            },
            "geometry": kml_record["geometry"],
        })
    return {
        "type": "FeatureCollection",
        "schema_version": 2,
        "artifact_status": "AUTHORITATIVE_INSTITUTIONAL_SOURCE_RECONCILIATION",
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "semantic_name_ar": SEMANTIC_NAME_AR,
        "semantic_name_en": SEMANTIC_NAME_EN,
        "excel_sha256": EXCEL_SHA256,
        "kml_sha256": KML_SHA256,
        "excel_record_count": 141,
        "kml_record_count": 141,
        "matched_count": 141,
        "raw_geometry_inventory": {"Polygon": 137, "MultiGeometry": 4},
        "deprecated_sources_used": False,
        "gdb_geometry_authority_used": False,
        "individual_investment_projects_included": False,
        "publication_approved": False,
        "features": features,
    }


def _vertex_count(geometry) -> int:
    if geometry.geom_type == "Polygon":
        return sum(len(ring.coords) for ring in [geometry.exterior, *geometry.interiors])
    if geometry.geom_type == "MultiPolygon":
        return sum(_vertex_count(part) for part in geometry.geoms)
    return 0


def _part_count(geometry) -> int:
    if geometry.geom_type == "Polygon":
        return 1
    if geometry.geom_type == "MultiPolygon":
        return len(geometry.geoms)
    return 0


def _metrics(geometry) -> dict:
    geojson = geojson_mapping(geometry)
    wkt = to_wkt(geometry, rounding_precision=-1)
    return {
        "geometry_type": geometry.geom_type,
        "valid": geometry.is_valid,
        "validity_reason": explain_validity(geometry),
        "empty": geometry.is_empty,
        "area_square_degrees": geometry.area,
        "centroid": [geometry.centroid.x, geometry.centroid.y],
        "bounds": list(geometry.bounds),
        "vertex_count": _vertex_count(geometry),
        "part_count": _part_count(geometry),
        "geojson": geojson,
        "geojson_sha256": geometry_hash(geojson),
        "wkt": wkt,
        "wkt_sha256": hashlib.sha256(wkt.encode("utf-8")).hexdigest(),
    }


def _polygonal_only(geometry):
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        return geometry, []
    polygon_parts = []
    discarded = []
    for part in getattr(geometry, "geoms", []):
        if part.geom_type == "Polygon":
            polygon_parts.append(part)
        elif part.geom_type == "MultiPolygon":
            polygon_parts.extend(part.geoms)
        else:
            discarded.append({
                "geometry_type": part.geom_type,
                "geojson": geojson_mapping(part),
                "geojson_sha256": geometry_hash(geojson_mapping(part)),
            })
    if not polygon_parts:
        return GeometryCollection(), discarded
    operational = polygon_parts[0] if len(polygon_parts) == 1 else MultiPolygon(polygon_parts)
    return operational, discarded


def _repair_fid_82(raw_geometry):
    before = _metrics(raw_geometry)
    if raw_geometry.is_valid:
        raise AuthoritativeInvestmentAreasError("FID 82 raw geometry was expected to be invalid")
    full_result = make_valid(raw_geometry)
    operational, discarded = _polygonal_only(full_result)
    after = _metrics(operational)
    area_delta = after["area_square_degrees"] - before["area_square_degrees"]
    area_delta_percent = 100 * area_delta / before["area_square_degrees"]
    centroid_shift = raw_geometry.centroid.distance(operational.centroid)
    symmetric_difference = raw_geometry.symmetric_difference(operational).area
    accepted = (
        after["valid"]
        and not after["empty"]
        and after["geometry_type"] in {"Polygon", "MultiPolygon"}
        and abs(area_delta_percent) <= 0.000001
        and centroid_shift <= 0.000000001
        and before["bounds"] == after["bounds"]
        and symmetric_difference <= 0.000000000001
        and after["part_count"] >= 1
    )
    provenance = {
        "fid": 82,
        "name_ar": "ترية",
        "source_geometry_status": "SOURCE_INVALID_TOPOLOGY",
        "operational_geometry_status": "VALIDATED_REPAIRED",
        "repair_approval_basis": REPAIR_BASIS,
        "repair_method": "GEOS_SHAPELY_MAKE_VALID_2_1_1_POLYGONAL_COMPONENTS_ONLY",
        "full_make_valid_result_type": full_result.geom_type,
        "discarded_non_polygonal_components": discarded,
        "before": before,
        "after": after,
        "area_delta_square_degrees": area_delta,
        "area_delta_percent": area_delta_percent,
        "centroid_shift_degrees": centroid_shift,
        "centroid_shift_approx_metres": centroid_shift * 111320,
        "bounds_equal": before["bounds"] == after["bounds"],
        "symmetric_difference_area_square_degrees": symmetric_difference,
        "acceptance_tolerances": {
            "maximum_absolute_area_delta_percent": 0.000001,
            "maximum_centroid_shift_degrees": 0.000000001,
            "maximum_symmetric_difference_square_degrees": 0.000000000001,
            "bounds_must_be_equal": True,
        },
        "accepted": accepted,
        "raw_source_overwritten": False,
    }
    if not accepted:
        raise AuthoritativeInvestmentAreasError("BLOCKED_GEOMETRY_REPAIR: FID 82 repair exceeded tolerance")
    return operational, provenance


def _cross_layer_candidates(governed_features: list[dict]) -> list[dict]:
    comparisons = {
        "HOTELS": GIS / "hotels-governed-import.review.geojson",
        "TOURISM_RESORTS": GIS / "tourism-resorts-governed-import.review.geojson",
        "PARKS": GIS / "parks-governed-import.review.geojson",
    }
    point_records = []
    for layer_code, path in comparisons.items():
        if not path.is_file():
            continue
        for feature in load(path).get("features", []):
            geometry = feature.get("geometry")
            if isinstance(geometry, dict) and geometry.get("type") == "Point":
                point = shape(geometry)
                if point.is_valid and not point.is_empty:
                    properties = feature.get("properties", {})
                    point_records.append((layer_code, point, properties))
    candidates = []
    for area_feature in governed_features:
        area = shape(area_feature["geometry"])
        for layer_code, point, properties in point_records:
            if area.covers(point):
                candidates.append({
                    "investment_area_institutional_id": area_feature["properties"]["institutional_id"],
                    "investment_area_fid": area_feature["properties"]["fid"],
                    "investment_area_name_ar": area_feature["properties"]["name_ar"],
                    "related_layer_code": layer_code,
                    "related_institutional_id": properties.get("institutional_id"),
                    "related_source_feature_id": properties.get("source_feature_id"),
                    "related_name_ar": properties.get("name_ar"),
                    "relationship": "SPATIAL_CONTAINMENT_CANDIDATE",
                    "geometric_test": "AUTHORITATIVE_OPERATIONAL_POLYGON_COVERS_SOURCE_POINT",
                    "institutional_relationship_established": False,
                    "publication_approved": False,
                })
    return sorted(
        candidates,
        key=lambda item: (
            item["investment_area_institutional_id"],
            item["related_layer_code"],
            str(item["related_institutional_id"]),
            str(item["related_source_feature_id"]),
        ),
    )


def build_governed(source: dict) -> tuple[dict, dict, dict]:
    if len(source.get("features", [])) != 141 or source.get("matched_count") != 141:
        raise AuthoritativeInvestmentAreasError("Authoritative source accounting failed")
    governed_features = []
    repair_provenance = None
    raw_inventory = Counter()
    operational_inventory = Counter()
    for source_feature in source["features"]:
        properties = source_feature["properties"]
        raw_inventory[properties["source_geometry_type"]] += 1
        raw_geometry = shape(source_feature["geometry"])
        fid = properties["fid"]
        if fid == 82:
            operational_geometry, repair_provenance = _repair_fid_82(raw_geometry)
            geometry_status = "VALIDATED_REPAIRED"
        else:
            if not raw_geometry.is_valid or raw_geometry.is_empty:
                raise AuthoritativeInvestmentAreasError(
                    f"Unexpected invalid authoritative geometry for {properties['source_feature_id']}"
                )
            if raw_geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                raise AuthoritativeInvestmentAreasError("Non-polygonal authoritative geometry")
            operational_geometry = raw_geometry
            geometry_status = "INSTITUTIONALLY_APPROVED_GEOMETRY"
        operational_inventory[operational_geometry.geom_type] += 1
        attributes = properties["source_attributes"]
        source_metadata = {
            "semantic_layer_code": SEMANTIC_LAYER_CODE,
            "source_excel_identity": properties["source_excel_identity"],
            "source_kml_identity": properties["source_kml_identity"],
            "source_attributes": attributes,
            "source_geometry_type": properties["source_geometry_type"],
            "source_geometry_geojson_sha256": properties["source_geometry_geojson_sha256"],
            "source_geometry_wkt_sha256": properties["source_geometry_wkt_sha256"],
            "source_geometry_valid": properties["source_geometry_valid"],
            "source_geometry_validity_reason": properties["source_geometry_validity_reason"],
            "operational_geometry_geojson_sha256": geometry_hash(geojson_mapping(operational_geometry)),
            "authority_status": "APPROVED",
            "review_status": "APPROVED",
            "canonical_identity_approved": True,
            "geometry_status": geometry_status,
            "institutional_approval_basis": APPROVAL_BASIS,
            "publication_approved": False,
            "is_published": False,
        }
        if fid == 82:
            source_metadata["geometry_repair_provenance"] = repair_provenance
        governed_features.append({
            "type": "Feature",
            "properties": {
                "feature_code": properties["institutional_id"],
                "institutional_id": properties["institutional_id"],
                "source_feature_id": properties["source_feature_id"],
                "fid": fid,
                "name_ar": properties["name_ar"],
                "name_en": properties["name_en"],
                "category": "tourism_investment",
                "semantic_layer_code": SEMANTIC_LAYER_CODE,
                "area_hectares_source": attributes.get("المساحة (هكتار)"),
                "calculated_square_kilometres_source": attributes.get("المساحة المحسوبة (كم2)"),
                "shape_length_source": attributes.get("محيط الشكل (Shape_Length)"),
                "representative_x_source": attributes.get("X (خط الطول - Longitude)"),
                "representative_y_source": attributes.get("Y (خط العرض - Latitude)"),
                "boundary_point_count_source": attributes.get("عدد نقاط الحدود"),
                "description_ar": attributes.get("الوصف"),
                "geometry_type": operational_geometry.geom_type,
                "geometry_status": geometry_status,
                "authority_status": "APPROVED",
                "review_status": "APPROVED",
                "canonical_identity_approved": True,
                "publication_approved": False,
                "is_published": False,
                "source_identity": (
                    f"{EXCEL.name}#{properties['source_feature_id']}|"
                    f"{KML.name}#Placemark-{properties['source_kml_identity']['placemark_position']}"
                ),
                "source_metadata": source_metadata,
            },
            "geometry": geojson_mapping(operational_geometry),
        })
    if repair_provenance is None:
        raise AuthoritativeInvestmentAreasError("FID 82 repair provenance missing")
    candidates = _cross_layer_candidates(governed_features)
    reconciliation = {
        "schema_version": 2,
        "inventory_id": "tourism-investment-areas-authoritative-reconciliation-v2",
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "excel_sha256": EXCEL_SHA256,
        "kml_sha256": KML_SHA256,
        "excel_record_count": 141,
        "kml_record_count": 141,
        "matched_count": 141,
        "approved_count": 141,
        "blocked_count": 0,
        "missing_identity_count": 0,
        "duplicate_identity_count": 0,
        "missing_geometry_count": 0,
        "fid_match_count": sum(item["properties"]["match_method"] == "INSTITUTIONAL_FID" for item in source["features"]),
        "exact_name_match_count": sum(item["properties"]["match_method"] == "NORMALIZED_EXACT_INSTITUTIONAL_NAME" for item in source["features"]),
        "raw_geometry_inventory": dict(sorted(raw_inventory.items())),
        "operational_geometry_inventory": dict(sorted(operational_inventory.items())),
        "fid_82_geometry_repair": repair_provenance,
        "authority_status": "APPROVED",
        "review_status": "APPROVED",
        "canonical_identity_approved": True,
        "publication_approved": False,
        "publication_state": "AWAITING_SEPARATE_PUBLICATION_GOVERNANCE",
    }
    governed_import = {
        "type": "FeatureCollection",
        "schema_version": 2,
        "name": "TOURISM DEVELOPMENT AND INVESTMENT AREAS approved governed import",
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "semantic_name_ar": SEMANTIC_NAME_AR,
        "semantic_name_en": SEMANTIC_NAME_EN,
        "excel_sha256": EXCEL_SHA256,
        "kml_sha256": KML_SHA256,
        "source_feature_count": 141,
        "approved_feature_count": 141,
        "blocked_feature_count": 0,
        "authority_status": "APPROVED",
        "review_status": "APPROVED",
        "canonical_identity_approved": True,
        "publication_approved": False,
        "is_published": False,
        "features": governed_features,
    }
    cross_layer = {
        "schema_version": 2,
        "inventory_id": "tourism-investment-areas-cross-layer-review-v2",
        "layer_code": LAYER_CODE,
        "semantic_layer_code": SEMANTIC_LAYER_CODE,
        "comparison_layers": ["HOTELS", "TOURISM_RESORTS", "PARKS"],
        "relationship_type": "SPATIAL_CONTAINMENT_CANDIDATE",
        "institutional_relationships_created": 0,
        "spatial_containment_candidate_count": len(candidates),
        "publication_approved": False,
        "records": candidates,
    }
    return reconciliation, governed_import, cross_layer


def validate() -> tuple[dict, dict, dict, dict]:
    if not SOURCE.is_file():
        raise AuthoritativeInvestmentAreasError(f"Missing source artifact: {SOURCE.name}")
    source = load(SOURCE)
    if source.get("excel_sha256") != EXCEL_SHA256 or source.get("kml_sha256") != KML_SHA256:
        raise AuthoritativeInvestmentAreasError("Committed source identity mismatch")
    built = build_governed(source)
    for path, artifact in zip((RECONCILIATION, IMPORT, CROSS), built):
        if not path.is_file() or path.read_bytes() != canonical_bytes(artifact):
            raise AuthoritativeInvestmentAreasError(f"Artifact missing or stale: {path.name}")
    reconciliation, governed_import, cross_layer = built
    if len(governed_import["features"]) != 141:
        raise AuthoritativeInvestmentAreasError("Governed import does not contain 141 features")
    if len({item["properties"]["institutional_id"] for item in governed_import["features"]}) != 141:
        raise AuthoritativeInvestmentAreasError("Duplicate governed institutional identity")
    return source, reconciliation, governed_import, cross_layer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        source = build_source()
        SOURCE.write_bytes(canonical_bytes(source))
        for path, artifact in zip((RECONCILIATION, IMPORT, CROSS), build_governed(source)):
            path.write_bytes(canonical_bytes(artifact))
    _, reconciliation, governed_import, cross_layer = validate()
    print("TOURISM INVESTMENT AREAS AUTHORITATIVE ARTIFACTS VALID")
    print("EXCEL:", reconciliation["excel_record_count"])
    print("KML:", reconciliation["kml_record_count"])
    print("MATCHED:", reconciliation["matched_count"])
    print("APPROVED:", reconciliation["approved_count"])
    print("BLOCKED:", reconciliation["blocked_count"])
    print("OPERATIONAL GEOMETRIES:", json.dumps(reconciliation["operational_geometry_inventory"], sort_keys=True))
    print("CROSS-LAYER CANDIDATES:", len(cross_layer["records"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
