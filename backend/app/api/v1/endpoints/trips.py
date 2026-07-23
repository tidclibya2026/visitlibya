from typing import Annotated, NoReturn

from fastapi import APIRouter, HTTPException, Path, status

from app.api.dependencies import CurrentActiveUserDependency, TripServiceDependency
from app.api.pagination import LimitParameter, SkipParameter
from app.core.exceptions import (
    DestinationUnavailableForTripError,
    DuplicateTripDestinationError,
    InvalidTripDateRangeError,
    InvalidTripDayError,
    InvalidTripItemOrderError,
    TripConcurrentModificationError,
    TripError,
    TripItemDateOutOfRangeError,
    TripItemNotFoundError,
    TripItemLimitExceededError,
    TripNotFoundError,
    TripPersistenceError,
)
from app.schemas.trip import (
    TripCreate,
    TripDetailResponse,
    TripItemCreate,
    TripItemReorderRequest,
    TripItemResponse,
    TripItemUpdate,
    TripListResponse,
    TripUpdate,
)


router = APIRouter(prefix="/trips", tags=["Trips"])
TripId = Annotated[int, Path(ge=1)]
ItemId = Annotated[int, Path(ge=1)]


def raise_http_error(error: TripError) -> NoReturn:
    if isinstance(error, (TripNotFoundError, TripItemNotFoundError)):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, (DuplicateTripDestinationError, TripConcurrentModificationError)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(
        error,
        (
            InvalidTripDateRangeError,
            InvalidTripDayError,
            TripItemDateOutOfRangeError,
            DestinationUnavailableForTripError,
            InvalidTripItemOrderError,
            TripItemLimitExceededError,
        ),
    ):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, TripPersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Trip service could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Trip request failed") from error


@router.post("", response_model=TripDetailResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripDetailResponse:
    try:
        return service.create_trip(user.id, payload)
    except TripError as error:
        raise_http_error(error)


@router.get("", response_model=TripListResponse)
def list_trips(
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
) -> TripListResponse:
    try:
        return service.list_user_trips(user.id, skip, limit)
    except TripError as error:
        raise_http_error(error)


@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(
    trip_id: TripId,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripDetailResponse:
    try:
        return service.get_trip(user.id, trip_id)
    except TripError as error:
        raise_http_error(error)


@router.patch("/{trip_id}", response_model=TripDetailResponse)
def update_trip(
    trip_id: TripId,
    payload: TripUpdate,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripDetailResponse:
    try:
        return service.update_trip(user.id, trip_id, payload)
    except TripError as error:
        raise_http_error(error)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: TripId,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> None:
    try:
        service.delete_trip(user.id, trip_id)
    except TripError as error:
        raise_http_error(error)


@router.post(
    "/{trip_id}/items",
    response_model=TripItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_trip_item(
    trip_id: TripId,
    payload: TripItemCreate,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripItemResponse:
    try:
        return service.add_trip_item(user.id, trip_id, payload)
    except TripError as error:
        raise_http_error(error)


@router.patch("/{trip_id}/items/{item_id}", response_model=TripItemResponse)
def update_trip_item(
    trip_id: TripId,
    item_id: ItemId,
    payload: TripItemUpdate,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripItemResponse:
    try:
        return service.update_trip_item(user.id, trip_id, item_id, payload)
    except TripError as error:
        raise_http_error(error)


@router.delete("/{trip_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip_item(
    trip_id: TripId,
    item_id: ItemId,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> None:
    try:
        service.delete_trip_item(user.id, trip_id, item_id)
    except TripError as error:
        raise_http_error(error)


@router.put("/{trip_id}/items/reorder", response_model=TripDetailResponse)
def reorder_trip_items(
    trip_id: TripId,
    payload: TripItemReorderRequest,
    user: CurrentActiveUserDependency,
    service: TripServiceDependency,
) -> TripDetailResponse:
    try:
        return service.reorder_trip_items(user.id, trip_id, payload)
    except TripError as error:
        raise_http_error(error)
