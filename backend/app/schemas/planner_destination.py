from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.models.destination import DestinationStatus
from app.models.destination_planner_profile import (
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)


class PlannerDestinationTranslation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_code: str
    name: str
    short_description: str | None
    visitor_information: str | None
    accessibility_information: str | None


class PlannerDestinationOperationalData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommended_visit_minutes: int | None
    minimum_visit_minutes: int | None
    maximum_visit_minutes: int | None
    opening_hours: dict[str, Any] | None
    opening_hours_timezone: str | None
    access_status: PlannerAccessStatus | None
    road_access: PlannerRoadAccess | None
    road_surface: PlannerRoadSurface | None
    road_condition: PlannerRoadCondition | None
    planner_priority: int | None
    meal_suitability: int | None
    rest_suitability: int | None
    data_source: str | None


class PlannerDestinationAuthority(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination_id: int
    slug: str
    category_code: str | None
    latitude: float | None
    longitude: float | None
    municipality: str | None
    region: str | None
    editorial_priority_order: int
    publication_status: DestinationStatus
    is_active: bool
    translations: list[PlannerDestinationTranslation]
    profile_state: Literal["missing", "unverified", "reviewed", "verified"]
    profile_verification_status: PlannerVerificationStatus | None
    profile_verified_at: datetime | None
    operational_data: PlannerDestinationOperationalData

