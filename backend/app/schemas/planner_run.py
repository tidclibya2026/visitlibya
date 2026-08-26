from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.planner_run import PlannerRunStatus


class PlannerRunCreate(BaseModel):
    trip_id: int | None = Field(default=None, gt=0)
    planner_version: int = Field(default=1, ge=1)
    engine_version: str = Field(
        default="visitlibya-ai-planner-v1",
        min_length=1,
        max_length=64,
    )
    feasibility_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    input_snapshot: dict[str, Any]
    itinerary_snapshot: dict[str, Any]
    feasibility_snapshot: dict[str, Any]
    recommendations_snapshot: dict[str, Any]
    optimization_snapshot: dict[str, Any]


class PlannerRunEvidenceUpdate(BaseModel):
    feasibility_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    feasibility_snapshot: dict[str, Any]
    recommendations_snapshot: dict[str, Any]
    optimization_snapshot: dict[str, Any]


class PlannerRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int | None
    user_id: int

    planner_version: int
    engine_version: str
    status: PlannerRunStatus
    feasibility_score: int | None

    input_snapshot: dict[str, Any]
    itinerary_snapshot: dict[str, Any]
    feasibility_snapshot: dict[str, Any]
    recommendations_snapshot: dict[str, Any]
    optimization_snapshot: dict[str, Any]

    created_at: datetime
    updated_at: datetime


class PlannerRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int | None
    planner_version: int
    engine_version: str
    status: PlannerRunStatus
    feasibility_score: int | None
    created_at: datetime
    updated_at: datetime
