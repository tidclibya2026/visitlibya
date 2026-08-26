from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import (
    DestinationPlannerProfileServiceDependency,
    require_content_admin,
)
from app.core.exceptions import (
    DestinationNotFoundError,
    DestinationPlannerProfileConflictError,
    DestinationPlannerProfileError,
    DestinationPlannerProfileIntegrityError,
    DestinationPlannerProfileNotFoundError,
    DestinationPlannerProfilePersistenceError,
    DestinationPlannerProfileValidationError,
)
from app.models.destination_planner_profile import DestinationPlannerProfile
from app.schemas.destination_planner_profile import (
    DestinationPlannerProfileCreate,
    DestinationPlannerProfileCreateRequest,
    DestinationPlannerProfileRead,
    DestinationPlannerProfileUpdate,
)


router = APIRouter(
    prefix="/destinations/{destination_id}/planner-profile",
    tags=["Destination Planner Profiles"],
    dependencies=[Depends(require_content_admin)],
)
DestinationId = Annotated[int, Path(ge=1)]


def raise_http_error(error: Exception) -> NoReturn:
    if isinstance(
        error,
        (DestinationNotFoundError, DestinationPlannerProfileNotFoundError),
    ):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(
        error,
        (DestinationPlannerProfileConflictError, DestinationPlannerProfileIntegrityError),
    ):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, DestinationPlannerProfileValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, DestinationPlannerProfilePersistenceError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Destination planner profile service is unavailable",
        ) from error
    raise HTTPException(
        status_code=500,
        detail="Destination planner profile request failed",
    ) from error


@router.get("", response_model=DestinationPlannerProfileRead)
def get_destination_planner_profile(
    destination_id: DestinationId,
    service: DestinationPlannerProfileServiceDependency,
) -> DestinationPlannerProfile:
    try:
        return service.get_profile(destination_id)
    except (DestinationPlannerProfileError, DestinationNotFoundError) as error:
        raise_http_error(error)


@router.post(
    "",
    response_model=DestinationPlannerProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_destination_planner_profile(
    destination_id: DestinationId,
    payload: DestinationPlannerProfileCreateRequest,
    service: DestinationPlannerProfileServiceDependency,
) -> DestinationPlannerProfile:
    try:
        return service.create_profile(
            DestinationPlannerProfileCreate(
                destination_id=destination_id,
                **payload.model_dump(),
            )
        )
    except (DestinationPlannerProfileError, DestinationNotFoundError) as error:
        raise_http_error(error)


@router.patch("", response_model=DestinationPlannerProfileRead)
def update_destination_planner_profile(
    destination_id: DestinationId,
    payload: DestinationPlannerProfileUpdate,
    service: DestinationPlannerProfileServiceDependency,
) -> DestinationPlannerProfile:
    try:
        return service.update_profile(
            destination_id=destination_id,
            payload=payload,
        )
    except (DestinationPlannerProfileError, DestinationNotFoundError) as error:
        raise_http_error(error)
