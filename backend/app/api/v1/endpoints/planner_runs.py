from typing import Annotated, NoReturn

from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import CurrentActiveUserDependency, PlannerRunServiceDependency
from app.core.exceptions import TripNotFoundError
from app.models.planner_run import PlannerRun
from app.schemas.planner_run import (
    PlannerRunCreate,
    PlannerRunEvidenceUpdate,
    PlannerRunResponse,
    PlannerRunSummaryResponse,
)


router = APIRouter(tags=["Planner Runs"])
RunId = Annotated[int, Path(ge=1)]
TripId = Annotated[int, Path(ge=1)]
Skip = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


def raise_http_error(error: Exception, service: PlannerRunServiceDependency) -> NoReturn:
    if isinstance(error, TripNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, ValueError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, SQLAlchemyError):
        service.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Planner run service is unavailable",
        ) from error
    raise HTTPException(status_code=500, detail="Planner run request failed") from error


def require_run(run: PlannerRun | None) -> PlannerRun:
    if run is None:
        raise HTTPException(status_code=404, detail="Planner run not found")
    return run


@router.post("/planner-runs", response_model=PlannerRunResponse, status_code=201)
def create_planner_run(
    payload: PlannerRunCreate,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return service.create_run(user_id=user.id, **payload.model_dump())
    except (TripNotFoundError, ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.get("/planner-runs", response_model=list[PlannerRunSummaryResponse])
def list_planner_runs(
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
    skip: Skip = 0,
    limit: Limit = 50,
) -> list[PlannerRun]:
    try:
        return list(service.list_user_runs(user_id=user.id, skip=skip, limit=limit))
    except (ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.get("/planner-runs/{planner_run_id}", response_model=PlannerRunResponse)
def get_planner_run(
    planner_run_id: RunId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.get_owned_run(planner_run_id=planner_run_id, user_id=user.id))
    except SQLAlchemyError as error:
        raise_http_error(error, service)


@router.post("/planner-runs/{planner_run_id}/accept", response_model=PlannerRunResponse)
def accept_planner_run(
    planner_run_id: RunId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.accept_run(planner_run_id=planner_run_id, user_id=user.id))
    except (TripNotFoundError, ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.post("/planner-runs/{planner_run_id}/reject", response_model=PlannerRunResponse)
def reject_planner_run(
    planner_run_id: RunId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.reject_run(planner_run_id=planner_run_id, user_id=user.id))
    except (ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.patch("/planner-runs/{planner_run_id}/evidence", response_model=PlannerRunResponse)
def update_planner_run_evidence(
    planner_run_id: RunId,
    payload: PlannerRunEvidenceUpdate,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.update_evidence(
            planner_run_id=planner_run_id,
            user_id=user.id,
            **payload.model_dump(),
        ))
    except (ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.get("/trips/{trip_id}/planner-runs", response_model=list[PlannerRunSummaryResponse])
def list_trip_planner_runs(
    trip_id: TripId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
    skip: Skip = 0,
    limit: Limit = 50,
) -> list[PlannerRun]:
    try:
        return list(service.list_trip_runs(trip_id=trip_id, user_id=user.id, skip=skip, limit=limit))
    except (TripNotFoundError, ValueError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.get("/trips/{trip_id}/planner-runs/latest", response_model=PlannerRunResponse)
def get_latest_trip_planner_run(
    trip_id: TripId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.get_latest_trip_run(trip_id=trip_id, user_id=user.id))
    except (TripNotFoundError, SQLAlchemyError) as error:
        raise_http_error(error, service)


@router.get("/trips/{trip_id}/planner-runs/latest-accepted", response_model=PlannerRunResponse)
def get_latest_accepted_trip_planner_run(
    trip_id: TripId,
    user: CurrentActiveUserDependency,
    service: PlannerRunServiceDependency,
) -> PlannerRun:
    try:
        return require_run(service.get_latest_accepted_trip_run(trip_id=trip_id, user_id=user.id))
    except (TripNotFoundError, SQLAlchemyError) as error:
        raise_http_error(error, service)
