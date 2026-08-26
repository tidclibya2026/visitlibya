from collections.abc import Callable
from typing import Any

from app.core.exceptions import (
    DestinationUnavailableForTripError,
    PlannerExecutionError,
)
from app.core.planner_audit import log_planner_event
from app.models.destination import DestinationStatus
from app.models.planner_run import PlannerRun
from app.planner.execution import execute_planner
from app.schemas.planner_destination import PlannerDestinationAuthority
from app.schemas.planner_run import PlannerExecutionRequest
from app.services.planner_destination import PlannerDestinationAuthorityService
from app.services.planner_run import PlannerRunService


PLANNER_VERSION = 1
ENGINE_VERSION = "visitlibya-python-planner-v1"


class PlannerExecutionService:
    """Owner-scoped orchestration around the pure deterministic planner."""

    def __init__(
        self,
        authority_service: PlannerDestinationAuthorityService,
        planner_run_service: PlannerRunService,
        *,
        executor: Callable[[list[dict[str, Any]], dict[str, Any]], dict[str, Any]] = execute_planner,
        audit_logger: Callable[..., None] = log_planner_event,
    ) -> None:
        self.authority_service = authority_service
        self.planner_run_service = planner_run_service
        self.executor = executor
        self.audit_logger = audit_logger

    def execute(
        self,
        *,
        actor_id: int,
        trip_id: int,
        payload: PlannerExecutionRequest,
        request_id: str | None = None,
    ) -> tuple[PlannerRun, dict[str, Any], list[PlannerDestinationAuthority]]:
        self.planner_run_service.require_owned_trip(
            trip_id=trip_id,
            user_id=actor_id,
        )
        authorities = self._resolve_authorities(payload)
        preferences = {
            "days": payload.days,
            "pace": payload.pace,
            "startingPoint": payload.starting_point,
            "interests": payload.interests,
            "travelerType": payload.traveler_type,
        }
        authority_snapshot = [item.model_dump(mode="json") for item in authorities]
        try:
            result = self.executor(authority_snapshot, preferences)
            feasibility_score = result["feasibility"]["score"]
            itinerary_snapshot = {
                "days": result["days"],
                "selectedCount": result["selectedCount"],
                "requestedDays": result["requestedDays"],
                "pace": result["pace"],
            }
            feasibility_snapshot = result["feasibility"]
            recommendations_snapshot = result["recommendations"]
            optimization_snapshot = result["optimization"]
        except Exception as exc:
            raise PlannerExecutionError() from exc

        input_snapshot = {
            "destination_ids": [item.destination_id for item in authorities],
            "requested_destination_ids": payload.destination_ids,
            "requested_destination_slugs": payload.destination_slugs,
            "preferences": preferences,
            "destination_authority": authority_snapshot,
        }
        planner_run = self.planner_run_service.create_run(
            user_id=actor_id,
            trip_id=trip_id,
            planner_version=PLANNER_VERSION,
            engine_version=ENGINE_VERSION,
            feasibility_score=feasibility_score,
            input_snapshot=input_snapshot,
            itinerary_snapshot=itinerary_snapshot,
            feasibility_snapshot=feasibility_snapshot,
            recommendations_snapshot=recommendations_snapshot,
            optimization_snapshot=optimization_snapshot,
        )
        self.audit_logger(
            "planner_run_executed",
            actor_id=actor_id,
            request_id=request_id,
            planner_run_id=planner_run.id,
            trip_id=trip_id,
            status=planner_run.status.value,
        )
        return planner_run, result, authorities

    def rollback(self) -> None:
        self.planner_run_service.rollback()

    def _resolve_authorities(
        self,
        payload: PlannerExecutionRequest,
    ) -> list[PlannerDestinationAuthority]:
        authorities = [
            self.authority_service.get_authority(destination_id)
            for destination_id in payload.destination_ids
        ]
        authorities.extend(
            self.authority_service.get_authority_by_slug(slug)
            for slug in payload.destination_slugs
        )
        resolved_ids = [item.destination_id for item in authorities]
        if len(set(resolved_ids)) != len(resolved_ids):
            raise ValueError("destination identifiers resolve to duplicates")
        for authority in authorities:
            if (
                authority.publication_status != DestinationStatus.PUBLISHED
                or not authority.is_active
            ):
                raise DestinationUnavailableForTripError()
        return authorities
