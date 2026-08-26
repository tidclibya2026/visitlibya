from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DestinationNotFoundError, DestinationPersistenceError
from app.models.destination import Destination
from app.repositories.destination import DestinationRepository
from app.schemas.planner_destination import (
    PlannerDestinationAuthority,
    PlannerDestinationOperationalData,
    PlannerDestinationTranslation,
)


class PlannerDestinationAuthorityService:
    """Assemble deterministic planner input without granting publication authority."""

    def __init__(
        self,
        session: Session,
        repository: DestinationRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or DestinationRepository(session)

    def get_authority(self, destination_id: int) -> PlannerDestinationAuthority:
        if destination_id < 1:
            raise ValueError("destination_id must be positive")
        try:
            destination = self.repository.get_planner_authority_by_id(destination_id)
        except SQLAlchemyError as exc:
            if not self.session.is_active:
                self.session.rollback()
            raise DestinationPersistenceError() from exc
        if destination is None:
            raise DestinationNotFoundError()
        return self.assemble(destination)

    def get_authority_by_slug(self, slug: str) -> PlannerDestinationAuthority:
        normalized = slug.strip().lower()
        if not normalized:
            raise ValueError("destination slug must not be empty")
        try:
            destination = self.repository.get_planner_authority_by_slug(normalized)
        except SQLAlchemyError as exc:
            if not self.session.is_active:
                self.session.rollback()
            raise DestinationPersistenceError() from exc
        if destination is None:
            raise DestinationNotFoundError()
        return self.assemble(destination)

    @classmethod
    def assemble(cls, destination: Destination) -> PlannerDestinationAuthority:
        profile = destination.planner_profile
        translations = sorted(
            (
                PlannerDestinationTranslation(
                    language_code=item.language_code,
                    name=item.name,
                    short_description=item.short_description,
                    visitor_information=item.visitor_information,
                    accessibility_information=item.accessibility_information,
                )
                for item in destination.translations
            ),
            key=lambda item: item.language_code,
        )

        if profile is None:
            state = "missing"
            verification_status = None
            verified_at = None
            operational = PlannerDestinationOperationalData(
                recommended_visit_minutes=None,
                minimum_visit_minutes=None,
                maximum_visit_minutes=None,
                opening_hours=None,
                opening_hours_timezone=None,
                access_status=None,
                road_access=None,
                road_surface=None,
                road_condition=None,
                planner_priority=None,
                meal_suitability=None,
                rest_suitability=None,
                data_source=None,
            )
        else:
            verification_status = profile.verification_status
            state = verification_status.value
            verified_at = profile.verified_at
            operational = PlannerDestinationOperationalData(
                recommended_visit_minutes=profile.recommended_visit_minutes,
                minimum_visit_minutes=profile.minimum_visit_minutes,
                maximum_visit_minutes=profile.maximum_visit_minutes,
                opening_hours=cls._stable_mapping(profile.opening_hours),
                opening_hours_timezone=profile.opening_hours_timezone,
                access_status=profile.access_status,
                road_access=profile.road_access,
                road_surface=profile.road_surface,
                road_condition=profile.road_condition,
                planner_priority=profile.planner_priority,
                meal_suitability=profile.meal_suitability,
                rest_suitability=profile.rest_suitability,
                data_source=profile.data_source,
            )

        return PlannerDestinationAuthority(
            destination_id=destination.id,
            slug=destination.slug,
            category_code=destination.category.code if destination.category else None,
            latitude=destination.latitude,
            longitude=destination.longitude,
            municipality=destination.municipality,
            region=destination.region,
            editorial_priority_order=destination.priority_order,
            publication_status=destination.status,
            is_active=destination.is_active,
            translations=translations,
            profile_state=state,
            profile_verification_status=verification_status,
            profile_verified_at=verified_at,
            operational_data=operational,
        )

    @classmethod
    def _stable_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        return {key: cls._stable_value(value[key]) for key in sorted(value)}

    @classmethod
    def _stable_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return cls._stable_mapping(value)
        if isinstance(value, list):
            return [cls._stable_value(item) for item in value]
        return value
