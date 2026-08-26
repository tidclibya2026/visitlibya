from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.planner_run import PlannerRunStatus
from app.schemas.planner_destination import PlannerDestinationAuthority


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


class PlannerExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination_ids: list[int] = Field(default_factory=list, max_length=50)
    destination_slugs: list[str] = Field(default_factory=list, max_length=50)
    days: int = Field(default=3, ge=1, le=14)
    pace: str = Field(default="balanced", pattern="^(relaxed|balanced|active)$")
    starting_point: str = Field(min_length=1, max_length=50)
    interests: list[str] = Field(default_factory=list, max_length=20)
    traveler_type: str = Field(default="", max_length=50)

    @model_validator(mode="after")
    def validate_destinations(self) -> "PlannerExecutionRequest":
        if not self.destination_ids and not self.destination_slugs:
            raise ValueError("at least one destination identifier is required")
        if len(set(self.destination_ids)) != len(self.destination_ids):
            raise ValueError("destination_ids must be unique")
        normalized = [value.strip().lower() for value in self.destination_slugs]
        if any(not value for value in normalized):
            raise ValueError("destination_slugs must not contain empty values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("destination_slugs must be unique")
        self.destination_slugs = normalized
        self.starting_point = self.starting_point.strip().lower()
        self.interests = [value.strip().lower() for value in self.interests if value.strip()]
        self.traveler_type = self.traveler_type.strip().lower()
        return self


class PlannerExecutionResponse(BaseModel):
    planner_run: PlannerRunResponse
    result: dict[str, Any]
    authority: list[PlannerDestinationAuthority]
