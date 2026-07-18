from typing import Annotated, NoReturn

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DestinationServiceDependency
from app.core.exceptions import (
    CategoryNotFoundError,
    DestinationCoordinatesError,
    DestinationError,
    DestinationIntegrityError,
    DestinationNotFoundError,
    DestinationPersistenceError,
    DestinationSlugConflictError,
    DestinationTranslationConflictError,
)
from app.models.destination import Destination, DestinationStatus
from app.schemas.destination import (
    DestinationCreate,
    DestinationListResponse,
    DestinationRead,
    DestinationUpdate,
)


router = APIRouter(prefix="/destinations", tags=["Destinations"])


def raise_http_error(error: DestinationError) -> NoReturn:
    if isinstance(error, DestinationNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, DestinationSlugConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, DestinationTranslationConflictError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, (CategoryNotFoundError, DestinationCoordinatesError)):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, DestinationIntegrityError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, DestinationPersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Destination service could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Destination request failed") from error


@router.get("", response_model=DestinationListResponse)
def list_destinations(
    service: DestinationServiceDependency,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[DestinationStatus | None, Query(alias="status")] = None,
    category_id: int | None = None,
    region: str | None = None,
    municipality: str | None = None,
    is_featured: bool | None = None,
    is_active: bool | None = True,
) -> DestinationListResponse:
    try:
        items, total = service.list_destinations(
            skip=skip,
            limit=limit,
            status=status_filter,
            category_id=category_id,
            region=region,
            municipality=municipality,
            is_featured=is_featured,
            is_active=is_active,
        )
    except DestinationError as error:
        raise_http_error(error)
    return DestinationListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
def create_destination(
    payload: DestinationCreate,
    service: DestinationServiceDependency,
) -> Destination:
    try:
        return service.create_destination(payload)
    except DestinationError as error:
        raise_http_error(error)


@router.get("/{slug}", response_model=DestinationRead)
def get_destination(
    slug: str,
    service: DestinationServiceDependency,
) -> Destination:
    try:
        return service.get_destination_by_slug(slug)
    except DestinationError as error:
        raise_http_error(error)


@router.put("/{destination_id}", response_model=DestinationRead)
def update_destination(
    destination_id: int,
    payload: DestinationUpdate,
    service: DestinationServiceDependency,
) -> Destination:
    try:
        return service.update_destination(destination_id, payload)
    except DestinationError as error:
        raise_http_error(error)


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_destination(
    destination_id: int,
    service: DestinationServiceDependency,
) -> None:
    try:
        service.delete_destination(destination_id)
    except DestinationError as error:
        raise_http_error(error)
