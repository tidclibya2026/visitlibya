from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GeometryFamily(StrEnum):
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    MIXED = "mixed"


class AuthorityLevel(StrEnum):
    INSTITUTIONAL = "institutional"
    SPECIALIZED_AUTHORITY = "specialized_authority"


class PublicationPolicy(StrEnum):
    EXPLICIT_INSTITUTIONAL_APPROVAL = "explicit_institutional_approval"
    SPECIALIZED_GOVERNED_WORKFLOW = "specialized_governed_workflow"


GEOMETRY_TYPES_BY_FAMILY: dict[GeometryFamily, frozenset[str]] = {
    GeometryFamily.POINT: frozenset({"POINT", "MULTIPOINT"}),
    GeometryFamily.LINE: frozenset({"LINESTRING", "MULTILINESTRING"}),
    GeometryFamily.POLYGON: frozenset({"POLYGON", "MULTIPOLYGON"}),
    GeometryFamily.MIXED: frozenset(
        {
            "POINT", "MULTIPOINT", "LINESTRING", "MULTILINESTRING",
            "POLYGON", "MULTIPOLYGON",
        }
    ),
}


@dataclass(frozen=True)
class GovernedGISLayer:
    layer_code: str
    name_ar: str
    name_en: str
    category: str
    geometry_family: GeometryFamily
    allowed_geometry_types: frozenset[str]
    source_owner: str
    institutional_reference: str
    authority_level: AuthorityLevel
    publication_policy: PublicationPolicy
    frontend_visibility: bool
    default_is_published: bool
    notes: str
    specialized_authority: bool = False


SOURCE_OWNER = "مركز المعلومات والتوثيق السياحي"
INSTITUTIONAL_REFERENCE = "مصادر نظم المعلومات الجغرافية المؤسسية"


def _layer(
    code: str,
    name_ar: str,
    name_en: str,
    category: str,
    family: GeometryFamily,
    notes: str,
    *,
    specialized: bool = False,
    allowed_geometry_types: frozenset[str] | None = None,
    institutional_reference: str = INSTITUTIONAL_REFERENCE,
) -> GovernedGISLayer:
    return GovernedGISLayer(
        layer_code=code,
        name_ar=name_ar,
        name_en=name_en,
        category=category,
        geometry_family=family,
        allowed_geometry_types=(
            allowed_geometry_types or GEOMETRY_TYPES_BY_FAMILY[family]
        ),
        source_owner=SOURCE_OWNER,
        institutional_reference=institutional_reference,
        authority_level=(
            AuthorityLevel.SPECIALIZED_AUTHORITY
            if specialized else AuthorityLevel.INSTITUTIONAL
        ),
        publication_policy=(
            PublicationPolicy.SPECIALIZED_GOVERNED_WORKFLOW
            if specialized else PublicationPolicy.EXPLICIT_INSTITUTIONAL_APPROVAL
        ),
        frontend_visibility=True,
        default_is_published=False,
        notes=notes,
        specialized_authority=specialized,
    )


LAYER_REGISTRY: dict[str, GovernedGISLayer] = {
    layer.layer_code: layer
    for layer in (
        _layer(
            "LIBYA_BOUNDARY", "الحدود الوطنية لليبيا", "Libya National Boundary",
            "national_boundary", GeometryFamily.POLYGON,
            "Remains authoritative in the specialized national_boundaries table.",
            specialized=True,
            institutional_reference="المخطط العام للتنمية السياحية",
        ),
        _layer(
            "WORLD_HERITAGE", "مواقع التراث العالمي", "World Heritage Sites",
            "heritage", GeometryFamily.MIXED,
            "Reserved for institutionally reviewed World Heritage GIS features.",
            allowed_geometry_types=frozenset(
                {"POINT", "MULTIPOINT", "POLYGON", "MULTIPOLYGON"}
            ),
        ),
        _layer(
            "OLD_TRIPOLI", "مدينة طرابلس القديمة", "Old City of Tripoli",
            "heritage", GeometryFamily.MIXED,
            "Reserved for reviewed Old Tripoli features; no boundary is inferred.",
        ),
        _layer(
            "NATURAL_SITES", "المواقع الطبيعية", "Natural Tourism Sites",
            "natural_tourism", GeometryFamily.MIXED,
            "Reserved for approved institutional natural-tourism GIS features.",
        ),
        _layer(
            "ARCHAEOLOGICAL_SITES", "المواقع الأثرية", "Archaeological Sites",
            "archaeology", GeometryFamily.MIXED,
            "Reserved for institutionally resolved archaeological features.",
        ),
        _layer(
            "FORTIFICATIONS", "القلاع والحصون", "Fortifications",
            "fortification", GeometryFamily.MIXED,
            "Reserved for institutionally resolved castles, forts, fortresses, and defensive structures.",
        ),
        _layer(
            "HISTORICAL_SITES", "المواقع التاريخية", "Historical Sites",
            "history", GeometryFamily.MIXED,
            "Reserved for institutionally resolved historical features.",
        ),
        _layer(
            "ROCK_ART", "الفنون الصخرية", "Rock Art",
            "rock_art", GeometryFamily.MIXED,
            "Reserved for reviewed rock-art features and sites.",
            allowed_geometry_types=frozenset(
                {"POINT", "MULTIPOINT", "POLYGON", "MULTIPOLYGON"}
            ),
        ),
    )
}


def normalize_layer_code(layer_code: str) -> str:
    return layer_code.strip().upper().replace("-", "_")


def get_layer(layer_code: str) -> GovernedGISLayer | None:
    return LAYER_REGISTRY.get(normalize_layer_code(layer_code))


def require_layer(layer_code: str) -> GovernedGISLayer:
    normalized = normalize_layer_code(layer_code)
    layer = LAYER_REGISTRY.get(normalized)
    if layer is None:
        raise ValueError(f"Unknown governed GIS layer: {normalized}")
    return layer


def public_layers() -> tuple[GovernedGISLayer, ...]:
    return tuple(layer for layer in LAYER_REGISTRY.values() if layer.frontend_visibility)
