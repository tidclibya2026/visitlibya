from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import DatabaseSession
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.schemas.destination import (
    DestinationCreate,
    DestinationListResponse,
    DestinationRead,
    DestinationTranslationCreate,
    DestinationUpdate,
)


router = APIRouter(prefix="/destinations", tags=["Destinations"])


def destination_options():
    return (
        selectinload(Destination.translations),
        selectinload(Destination.media_items),
    )


def get_destination_by_id(db: DatabaseSession, destination_id: int) -> Destination:
    destination = db.scalar(
        select(Destination)
        .options(*destination_options())
        .where(Destination.id == destination_id)
    )
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination


def apply_coordinates(destination: Destination) -> None:
    if destination.latitude is None or destination.longitude is None:
        destination.geometry = None
        return
    destination.geometry = WKTElement(
        f"POINT({destination.longitude} {destination.latitude})",
        srid=4326,
    )


def synchronize_translations(
    destination: Destination,
    translations: list[DestinationTranslationCreate],
) -> None:
    incoming = {item.language_code: item for item in translations}
    for existing in list(destination.translations):
        payload = incoming.pop(existing.language_code, None)
        if payload is None:
            destination.translations.remove(existing)
            continue
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
    destination.translations.extend(
        DestinationTranslation(**item.model_dump()) for item in incoming.values()
    )


@router.get("", response_model=DestinationListResponse)
def list_destinations(
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[DestinationStatus | None, Query(alias="status")] = None,
    category_id: int | None = None,
    region: str | None = None,
    municipality: str | None = None,
    is_featured: bool | None = None,
    is_active: bool | None = True,
) -> DestinationListResponse:
    filters = []
    if status_filter is not None:
        filters.append(Destination.status == status_filter)
    if category_id is not None:
        filters.append(Destination.category_id == category_id)
    if region is not None:
        filters.append(Destination.region == region)
    if municipality is not None:
        filters.append(Destination.municipality == municipality)
    if is_featured is not None:
        filters.append(Destination.is_featured == is_featured)
    if is_active is not None:
        filters.append(Destination.is_active == is_active)

    total = db.scalar(select(func.count(Destination.id)).where(*filters)) or 0
    items = db.scalars(
        select(Destination)
        .options(*destination_options())
        .where(*filters)
        .order_by(Destination.priority_order, Destination.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return DestinationListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
def create_destination(payload: DestinationCreate, db: DatabaseSession) -> Destination:
    if db.scalar(select(Destination.id).where(Destination.slug == payload.slug)) is not None:
        raise HTTPException(status_code=409, detail="Destination slug already exists")

    values = payload.model_dump(exclude={"translations"})
    destination = Destination(**values)
    destination.translations = [
        DestinationTranslation(**item.model_dump()) for item in payload.translations
    ]
    apply_coordinates(destination)
    db.add(destination)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Destination conflicts with existing data") from exc
    return get_destination_by_id(db, destination.id)


@router.get("/{slug}", response_model=DestinationRead)
def get_destination(slug: str, db: DatabaseSession) -> Destination:
    destination = db.scalar(
        select(Destination)
        .options(*destination_options())
        .where(Destination.slug == slug)
    )
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination


@router.put("/{destination_id}", response_model=DestinationRead)
def update_destination(
    destination_id: int,
    payload: DestinationUpdate,
    db: DatabaseSession,
) -> Destination:
    destination = get_destination_by_id(db, destination_id)
    values = payload.model_dump(exclude_unset=True, exclude={"translations"})

    new_slug = values.get("slug")
    if new_slug is not None:
        duplicate_id = db.scalar(
            select(Destination.id).where(
                Destination.slug == new_slug,
                Destination.id != destination_id,
            )
        )
        if duplicate_id is not None:
            raise HTTPException(status_code=409, detail="Destination slug already exists")

    for field, value in values.items():
        setattr(destination, field, value)

    if payload.translations is not None:
        synchronize_translations(destination, payload.translations)

    if "latitude" in values or "longitude" in values:
        if (destination.latitude is None) != (destination.longitude is None):
            raise HTTPException(
                status_code=422,
                detail="latitude and longitude must be provided together",
            )
        apply_coordinates(destination)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Destination conflicts with existing data") from exc
    return get_destination_by_id(db, destination.id)


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_destination(destination_id: int, db: DatabaseSession) -> None:
    destination = get_destination_by_id(db, destination_id)
    db.delete(destination)
    db.commit()
