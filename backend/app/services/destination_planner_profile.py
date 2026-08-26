from datetime import UTC, datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DestinationNotFoundError,
    DestinationPlannerProfileConflictError,
    DestinationPlannerProfileError,
    DestinationPlannerProfileIntegrityError,
    DestinationPlannerProfileNotFoundError,
    DestinationPlannerProfilePersistenceError,
    DestinationPlannerProfileValidationError,
)
from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)
from app.repositories.destination_planner_profile import (
    DestinationPlannerProfileRepository,
)
from app.schemas.destination_planner_profile import (
    DestinationPlannerProfileCreate,
    DestinationPlannerProfileUpdate,
)


class DestinationPlannerProfileService:
    def __init__(
        self,
        session: Session,
        repository: DestinationPlannerProfileRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = (
            repository
            or DestinationPlannerProfileRepository(session)
        )

    def get_profile(
        self,
        destination_id: int,
    ) -> DestinationPlannerProfile:
        self._validate_positive_id(destination_id, "destination_id")

        try:
            profile = self.repository.get_by_destination_id(
                destination_id
            )
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise DestinationPlannerProfilePersistenceError() from exc

        if profile is None:
            raise DestinationPlannerProfileNotFoundError()

        return profile

    def create_profile(
        self,
        payload: DestinationPlannerProfileCreate,
    ) -> DestinationPlannerProfile:
        self._validate_profile_values(
            destination_id=payload.destination_id,
            recommended_visit_minutes=payload.recommended_visit_minutes,
            minimum_visit_minutes=payload.minimum_visit_minutes,
            maximum_visit_minutes=payload.maximum_visit_minutes,
            planner_priority=payload.planner_priority,
            meal_suitability=payload.meal_suitability,
            rest_suitability=payload.rest_suitability,
        )

        try:
            if not self.repository.destination_exists(
                payload.destination_id
            ):
                raise DestinationNotFoundError()

            if self.repository.profile_exists_for_destination(
                payload.destination_id
            ):
                raise DestinationPlannerProfileConflictError()

            values = payload.model_dump()
            values["verified_at"] = self._verified_at_for_status(
                payload.verification_status,
                current=None,
            )

            profile = DestinationPlannerProfile(**values)

            self.repository.create_profile(profile)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(profile)

            return profile

        except (
            DestinationPlannerProfileError,
            DestinationNotFoundError,
        ):
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise DestinationPlannerProfileIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DestinationPlannerProfilePersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_profile(
        self,
        *,
        destination_id: int,
        payload: DestinationPlannerProfileUpdate,
    ) -> DestinationPlannerProfile:
        self._validate_positive_id(
            destination_id,
            "destination_id",
        )

        try:
            profile = self.repository.get_by_destination_id(
                destination_id
            )

            if profile is None:
                raise DestinationPlannerProfileNotFoundError()

            values = payload.model_dump(exclude_unset=True)

            candidate = {
                "recommended_visit_minutes": values.get(
                    "recommended_visit_minutes",
                    profile.recommended_visit_minutes,
                ),
                "minimum_visit_minutes": values.get(
                    "minimum_visit_minutes",
                    profile.minimum_visit_minutes,
                ),
                "maximum_visit_minutes": values.get(
                    "maximum_visit_minutes",
                    profile.maximum_visit_minutes,
                ),
                "planner_priority": values.get(
                    "planner_priority",
                    profile.planner_priority,
                ),
                "meal_suitability": values.get(
                    "meal_suitability",
                    profile.meal_suitability,
                ),
                "rest_suitability": values.get(
                    "rest_suitability",
                    profile.rest_suitability,
                ),
            }

            self._validate_profile_values(
                destination_id=destination_id,
                **candidate,
            )

            previous_verification_status = (
                profile.verification_status
            )

            for field, value in values.items():
                setattr(profile, field, value)

            if "verification_status" in values:
                profile.verified_at = (
                    self._verified_at_for_status(
                        profile.verification_status,
                        current=profile.verified_at,
                        previous_status=(
                            previous_verification_status
                        ),
                    )
                )

            self.repository.flush()
            self.session.commit()
            self.repository.refresh(profile)

            return profile

        except DestinationPlannerProfileError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise DestinationPlannerProfileIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DestinationPlannerProfilePersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    @classmethod
    def _validate_profile_values(
        cls,
        *,
        destination_id: int,
        recommended_visit_minutes: int | None,
        minimum_visit_minutes: int | None,
        maximum_visit_minutes: int | None,
        planner_priority: int,
        meal_suitability: int,
        rest_suitability: int,
    ) -> None:
        cls._validate_positive_id(
            destination_id,
            "destination_id",
        )

        durations = {
            "recommended_visit_minutes":
                recommended_visit_minutes,
            "minimum_visit_minutes":
                minimum_visit_minutes,
            "maximum_visit_minutes":
                maximum_visit_minutes,
        }

        for name, value in durations.items():
            if value is not None and value <= 0:
                raise DestinationPlannerProfileValidationError(
                    f"{name} must be positive"
                )

        if (
            minimum_visit_minutes is not None
            and recommended_visit_minutes is not None
            and minimum_visit_minutes
            > recommended_visit_minutes
        ):
            raise DestinationPlannerProfileValidationError(
                "minimum_visit_minutes cannot exceed "
                "recommended_visit_minutes"
            )

        if (
            maximum_visit_minutes is not None
            and recommended_visit_minutes is not None
            and maximum_visit_minutes
            < recommended_visit_minutes
        ):
            raise DestinationPlannerProfileValidationError(
                "maximum_visit_minutes cannot be below "
                "recommended_visit_minutes"
            )

        if (
            minimum_visit_minutes is not None
            and maximum_visit_minutes is not None
            and minimum_visit_minutes > maximum_visit_minutes
        ):
            raise DestinationPlannerProfileValidationError(
                "minimum_visit_minutes cannot exceed "
                "maximum_visit_minutes"
            )

        for name, value in {
            "planner_priority": planner_priority,
            "meal_suitability": meal_suitability,
            "rest_suitability": rest_suitability,
        }.items():
            if not 0 <= value <= 100:
                raise DestinationPlannerProfileValidationError(
                    f"{name} must be between 0 and 100"
                )

    @staticmethod
    def _validate_positive_id(
        value: int,
        name: str,
    ) -> None:
        if value < 1:
            raise DestinationPlannerProfileValidationError(
                f"{name} must be positive"
            )

    @staticmethod
    def _verified_at_for_status(
        status: PlannerVerificationStatus,
        *,
        current: datetime | None,
        previous_status: PlannerVerificationStatus | None = None,
    ) -> datetime | None:
        if status == PlannerVerificationStatus.VERIFIED:
            if (
                previous_status
                == PlannerVerificationStatus.VERIFIED
                and current is not None
            ):
                return current
            return datetime.now(UTC)

        return None

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
