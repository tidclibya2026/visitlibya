from typing import Annotated, NoReturn

from fastapi import APIRouter, HTTPException, Path, status

from app.api.dependencies import (
    CurrentActiveUserDependency,
    FavoriteServiceDependency,
)
from app.api.pagination import LimitParameter, SkipParameter
from app.core.exceptions import (
    DestinationNotFoundError,
    FavoriteError,
    FavoriteIntegrityError,
    FavoritePersistenceError,
)
from app.schemas.favorite import (
    FavoriteCheckResponse,
    FavoriteListResponse,
    FavoriteRead,
)


router = APIRouter(prefix="/favorites", tags=["Favorites"])
DestinationId = Annotated[int, Path(ge=1)]


def raise_http_error(error: Exception) -> NoReturn:
    if isinstance(error, DestinationNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, FavoriteIntegrityError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, FavoritePersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Favorite service could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Favorite request failed") from error


@router.post("/{destination_id}", response_model=FavoriteRead)
def add_favorite(
    destination_id: DestinationId,
    user: CurrentActiveUserDependency,
    service: FavoriteServiceDependency,
) -> FavoriteRead:
    try:
        return service.add_favorite(user.id, destination_id)
    except (FavoriteError, DestinationNotFoundError) as error:
        raise_http_error(error)


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    destination_id: DestinationId,
    user: CurrentActiveUserDependency,
    service: FavoriteServiceDependency,
) -> None:
    try:
        service.delete_favorite(user.id, destination_id)
    except FavoriteError as error:
        raise_http_error(error)


@router.get("", response_model=FavoriteListResponse)
def list_favorites(
    user: CurrentActiveUserDependency,
    service: FavoriteServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
) -> FavoriteListResponse:
    try:
        return service.list_favorites(user_id=user.id, skip=skip, limit=limit)
    except FavoriteError as error:
        raise_http_error(error)


@router.get("/check/{destination_id}", response_model=FavoriteCheckResponse)
def check_favorite(
    destination_id: DestinationId,
    user: CurrentActiveUserDependency,
    service: FavoriteServiceDependency,
) -> FavoriteCheckResponse:
    try:
        return service.check_favorite(user.id, destination_id)
    except (FavoriteError, DestinationNotFoundError) as error:
        raise_http_error(error)
