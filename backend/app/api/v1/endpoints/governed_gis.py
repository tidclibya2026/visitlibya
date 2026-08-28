from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.gis.layer_registry import GovernedGISLayer
from app.schemas.governed_gis import (
    GovernedGISFeatureCollection,
    GovernedGISFeatureList,
    GovernedGISGeoJSONFeature,
    GovernedGISLayerPublic,
)
from app.services.governed_gis import GovernedGISService


router = APIRouter(prefix="/gis/layers", tags=["Governed GIS Layers"])


def _layer_response(layer: GovernedGISLayer) -> dict:
    return {
        "layer_code": layer.layer_code,
        "name_ar": layer.name_ar,
        "name_en": layer.name_en,
        "category": layer.category,
        "geometry_family": layer.geometry_family.value,
        "allowed_geometry_types": sorted(layer.allowed_geometry_types),
        "authority_level": layer.authority_level.value,
        "publication_policy": layer.publication_policy.value,
        "frontend_visibility": layer.frontend_visibility,
        "notes": layer.notes,
        "specialized_authority": layer.specialized_authority,
    }


@router.get("", response_model=list[GovernedGISLayerPublic])
def list_governed_layers(session: Session = Depends(get_db)) -> list[dict]:
    return [_layer_response(layer) for layer in GovernedGISService(session).list_layers()]


@router.get("/{layer_code}", response_model=GovernedGISLayerPublic)
def get_governed_layer(layer_code: str, session: Session = Depends(get_db)) -> dict:
    layer = GovernedGISService(session).get_layer(layer_code)
    if layer is None:
        raise HTTPException(status_code=404, detail="Governed GIS layer not found")
    return _layer_response(layer)


@router.get("/{layer_code}/features", response_model=GovernedGISFeatureList)
def list_governed_features(
    layer_code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_db),
) -> dict:
    try:
        items = GovernedGISService(session).get_public_features(
            layer_code, skip=skip, limit=limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"items": items, "skip": skip, "limit": limit}


@router.get(
    "/{layer_code}/features/{feature_code}",
    response_model=GovernedGISGeoJSONFeature,
)
def get_governed_feature(
    layer_code: str, feature_code: str, session: Session = Depends(get_db)
) -> dict:
    try:
        feature = GovernedGISService(session).get_public_feature(
            layer_code, feature_code
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if feature is None:
        raise HTTPException(status_code=404, detail="Published GIS feature not found")
    return feature


@router.get("/{layer_code}/geojson", response_model=GovernedGISFeatureCollection)
def get_governed_layer_geojson(
    layer_code: str,
    limit: int = Query(1000, ge=1, le=5000),
    session: Session = Depends(get_db),
) -> dict:
    try:
        return GovernedGISService(session).get_public_geojson(layer_code, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{layer_code}/bbox", response_model=GovernedGISFeatureCollection)
def get_governed_layer_bbox(
    layer_code: str,
    min_longitude: float = Query(..., ge=-180, le=180),
    min_latitude: float = Query(..., ge=-90, le=90),
    max_longitude: float = Query(..., ge=-180, le=180),
    max_latitude: float = Query(..., ge=-90, le=90),
    limit: int = Query(1000, ge=1, le=5000),
    session: Session = Depends(get_db),
) -> dict:
    try:
        return GovernedGISService(session).get_public_bbox_geojson(
            layer_code,
            min_longitude=min_longitude,
            min_latitude=min_latitude,
            max_longitude=max_longitude,
            max_latitude=max_latitude,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

