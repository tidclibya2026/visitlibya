from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import MediaServiceDependency, require_content_admin
from app.api.pagination import LimitParameter, SkipParameter
from app.core.exceptions import (
    DestinationMediaConflictError,
    DestinationMediaNotFoundError,
    DestinationNotFoundError,
    MediaAssetIntegrityError,
    MediaAssetNotFoundError,
    MediaAssetPathConflictError,
    MediaAssetPersistenceError,
    MediaError,
)
from app.models.media import DestinationMedia, MediaAsset
from app.schemas.media import (
    DestinationMediaCreate,
    DestinationMediaRead,
    DestinationMediaUpdate,
    MediaAssetCreate,
    MediaAssetListResponse,
    MediaAssetRead,
    MediaAssetUpdate,
    MediaSortField,
    MediaSortOrder,
)


router = APIRouter(prefix="/media", tags=["Media"])


def raise_http_error(error: Exception) -> NoReturn:
    if isinstance(error, (MediaAssetNotFoundError, DestinationMediaNotFoundError, DestinationNotFoundError)):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, (MediaAssetPathConflictError, MediaAssetIntegrityError, DestinationMediaConflictError)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, MediaAssetPersistenceError):
        raise HTTPException(status_code=500, detail="Media service could not complete the request") from error
    raise HTTPException(status_code=500, detail="Media request failed") from error


@router.get("", response_model=MediaAssetListResponse)
def list_media(
    service: MediaServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
    mime_type: str | None = None,
    is_active: bool | None = True,
    destination_id: int | None = None,
    is_primary: bool | None = None,
    sort_by: MediaSortField = "id",
    sort_order: MediaSortOrder = "asc",
) -> MediaAssetListResponse:
    try:
        items, total = service.list_media(skip=skip, limit=limit, mime_type=mime_type, is_active=is_active, destination_id=destination_id, is_primary=is_primary, sort_by=sort_by, sort_order=sort_order)
    except MediaError as error:
        raise_http_error(error)
    return MediaAssetListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.post("", response_model=MediaAssetRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_content_admin)])
def create_media(payload: MediaAssetCreate, service: MediaServiceDependency) -> MediaAsset:
    try:
        return service.create_media(payload)
    except MediaError as error:
        raise_http_error(error)


@router.get("/{media_id}", response_model=MediaAssetRead)
def get_media(media_id: int, service: MediaServiceDependency) -> MediaAsset:
    try:
        return service.get_media(media_id)
    except MediaError as error:
        raise_http_error(error)


@router.put("/{media_id}", response_model=MediaAssetRead, dependencies=[Depends(require_content_admin)])
def update_media(media_id: int, payload: MediaAssetUpdate, service: MediaServiceDependency) -> MediaAsset:
    try:
        return service.update_media(media_id, payload)
    except MediaError as error:
        raise_http_error(error)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_content_admin)])
def delete_media(media_id: int, service: MediaServiceDependency) -> None:
    try:
        service.delete_media(media_id)
    except MediaError as error:
        raise_http_error(error)


@router.post("/{media_id}/destinations/{destination_id}", response_model=DestinationMediaRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_content_admin)])
def associate_destination(media_id: int, destination_id: int, payload: DestinationMediaCreate, service: MediaServiceDependency) -> DestinationMedia:
    try:
        return service.associate_destination(media_id, destination_id, payload)
    except (MediaError, DestinationNotFoundError) as error:
        raise_http_error(error)


@router.put("/{media_id}/destinations/{destination_id}", response_model=DestinationMediaRead, dependencies=[Depends(require_content_admin)])
def update_destination_link(media_id: int, destination_id: int, payload: DestinationMediaUpdate, service: MediaServiceDependency) -> DestinationMedia:
    try:
        return service.update_destination_link(media_id, destination_id, payload)
    except MediaError as error:
        raise_http_error(error)


@router.delete("/{media_id}/destinations/{destination_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_content_admin)])
def remove_destination(media_id: int, destination_id: int, service: MediaServiceDependency) -> None:
    try:
        service.remove_destination(media_id, destination_id)
    except MediaError as error:
        raise_http_error(error)
