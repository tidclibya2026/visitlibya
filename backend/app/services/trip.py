from collections.abc import Sequence
from datetime import date, time
import secrets

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DestinationUnavailableForTripError,
    InvalidTripDateRangeError,
    InvalidTripStatusTransitionError,
    InvalidTripDayError,
    InvalidTripItemOrderError,
    InvalidTripShareStateError,
    TripConcurrentModificationError,
    TripItemDateOutOfRangeError,
    TripItemLimitExceededError,
    TripItemNotFoundError,
    TripItemTimeConflictError,
    TripNotFoundError,
    TripPersistenceError,
)
from app.core.trip_constants import MAX_TRIP_ITEMS, TRIP_POSITION_RETRY_LIMIT
from app.models.destination import DestinationTranslation
from app.models.trip import Trip, TripStatus, TripVisibility
from app.models.trip_item import TripItem
from app.repositories.trip import TripRepository
from app.schemas.trip import (
    TripCloneRequest,
    TripCreate,
    TripDestinationSummary,
    TripDetailResponse,
    TripItemCreate,
    TripItemReorderRequest,
    TripItemResponse,
    TripItemUpdate,
    TripListResponse,
    TripOwnerDetailResponse,
    TripShareLinkRequest,
    TripSummaryResponse,
    TripUpdate,
)


class TripService:
    def __init__(self, session: Session, repository: TripRepository | None = None) -> None:
        self.session = session
        self.repository = repository or TripRepository(session)

    def create_trip(self, user_id: int, payload: TripCreate) -> TripDetailResponse:
        self._validate_date_range(payload.start_date, payload.end_date)
        if payload.status != TripStatus.DRAFT:
            raise InvalidTripStatusTransitionError()
        values = payload.model_dump()
        if payload.visibility == TripVisibility.UNLISTED:
            values["share_token"] = self._new_share_token()
        trip = Trip(user_id=user_id, **values)
        return self._write(lambda: self._create(trip))

    def _create(self, trip: Trip) -> TripOwnerDetailResponse:
        self.repository.create_trip(trip)
        self.repository.flush()
        self.session.commit()
        return self._owner_detail(trip)

    def list_user_trips(self, user_id: int, skip: int, limit: int) -> TripListResponse:
        if user_id < 1 or skip < 0 or not 1 <= limit <= 100:
            raise ValueError("Invalid trip list parameters")
        try:
            entries = self.repository.list_user_trips(user_id, skip, limit)
            total = self.repository.count_user_trips(user_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        return TripListResponse(
            items=[self._summary(entry.trip, entry.item_count) for entry in entries],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_trip(self, user_id: int, trip_id: int) -> TripOwnerDetailResponse:
        return self._owner_detail(self._owned_trip(user_id, trip_id))

    def get_public_trip(self, trip_id: int) -> TripDetailResponse:
        try:
            trip = self.repository.get_public_trip_by_id(trip_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        if trip is None:
            raise TripNotFoundError()
        return self._detail(trip)

    def get_shared_trip(self, share_token: str) -> TripDetailResponse:
        try:
            trip = self.repository.get_unlisted_trip_by_token(share_token)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        if trip is None:
            raise TripNotFoundError()
        return self._detail(trip)

    def update_trip(
        self, user_id: int, trip_id: int, payload: TripUpdate
    ) -> TripDetailResponse:
        trip = self._owned_trip(user_id, trip_id)
        changes = payload.model_dump(exclude_unset=True)
        expected_version = changes.pop("expected_version", None) or trip.version
        start_date = changes.get("start_date", trip.start_date)
        end_date = changes.get("end_date", trip.end_date)
        self._validate_date_range(start_date, end_date)
        self._validate_existing_items(trip.items, start_date, end_date)

        new_status = changes.get("status")
        if new_status is not None:
            self._validate_status_transition(trip, new_status)

        new_visibility = changes.get("visibility")
        if new_visibility is not None:
            if new_visibility == TripVisibility.UNLISTED:
                changes["share_token"] = trip.share_token or self._new_share_token()
            else:
                changes["share_token"] = None

        def operation() -> TripOwnerDetailResponse:
            next_version = self._increment_version(
                trip,
                user_id,
                expected_version,
            )
            for field, value in changes.items():
                setattr(trip, field, value)
            self.repository.flush()
            self.session.commit()
            trip.version = next_version
            return self._owner_detail(trip)

        return self._write(operation)

    def rotate_share_link(
        self,
        user_id: int,
        trip_id: int,
        payload: TripShareLinkRequest,
    ) -> TripOwnerDetailResponse:
        trip = self._owned_trip(user_id, trip_id)
        if trip.visibility != TripVisibility.UNLISTED:
            raise InvalidTripShareStateError()

        expected_version = payload.expected_version or trip.version

        def operation() -> TripOwnerDetailResponse:
            next_version = self._increment_version(
                trip,
                user_id,
                expected_version,
            )
            trip.share_token = self._new_share_token()
            self.repository.flush()
            self.session.commit()
            trip.version = next_version
            return self._owner_detail(trip)

        return self._write(operation)

    def revoke_share_link(
        self,
        user_id: int,
        trip_id: int,
        payload: TripShareLinkRequest,
    ) -> TripOwnerDetailResponse:
        trip = self._owned_trip(user_id, trip_id)
        if trip.visibility != TripVisibility.UNLISTED:
            raise InvalidTripShareStateError()

        expected_version = payload.expected_version or trip.version

        def operation() -> TripOwnerDetailResponse:
            next_version = self._increment_version(
                trip,
                user_id,
                expected_version,
            )
            trip.share_token = None
            self.repository.flush()
            self.session.commit()
            trip.version = next_version
            return self._owner_detail(trip)

        return self._write(operation)

    def clone_trip(
        self,
        user_id: int,
        trip_id: int,
        payload: TripCloneRequest,
    ) -> TripOwnerDetailResponse:
        source = self._owned_trip(user_id, trip_id)

        cloned = Trip(
            user_id=user_id,
            title=payload.title or f"{source.title} (Copy)",
            description=source.description,
            start_date=source.start_date,
            end_date=source.end_date,
            status=TripStatus.DRAFT,
            visibility=TripVisibility.PRIVATE,
            share_token=None,
            version=1,
        )

        cloned.items = [
            TripItem(
                destination_id=item.destination_id,
                destination=item.destination,
                day_number=item.day_number,
                visit_date=item.visit_date,
                start_time=item.start_time,
                duration_minutes=item.duration_minutes,
                sort_order=item.sort_order,
                notes=item.notes,
            )
            for item in source.items
        ]

        def operation() -> TripOwnerDetailResponse:
            self.repository.create_trip(cloned)
            self.repository.flush()
            self.session.commit()
            return self._owner_detail(cloned)

        return self._write(operation)

    def delete_trip(self, user_id: int, trip_id: int) -> None:
        trip = self._owned_trip(user_id, trip_id)

        def operation() -> None:
            self.repository.delete_trip(trip)
            self.repository.flush()
            self.session.commit()

        self._write(operation)

    def add_trip_item(
        self, user_id: int, trip_id: int, payload: TripItemCreate
    ) -> TripItemResponse:
        trip = self._owned_trip(user_id, trip_id)
        expected_version = payload.expected_version or trip.version

        def operation() -> TripItemResponse:
            if self.repository.count_trip_items(trip.id) >= MAX_TRIP_ITEMS:
                raise TripItemLimitExceededError()
            destination = self._public_destination(payload.destination_id)
            day_number, visit_date = self._resolve_item_date(
                trip, payload.day_number, payload.visit_date
            )
            self._assert_no_time_conflict(
                trip.items,
                day_number,
                payload.start_time,
                payload.duration_minutes,
            )
            attempts = TRIP_POSITION_RETRY_LIMIT if payload.sort_order is None else 1
            next_version = self._increment_version(
                trip,
                user_id,
                expected_version,
            )
            for attempt in range(attempts):
                sort_order = (
                    payload.sort_order
                    if payload.sort_order is not None
                    else self.repository.next_sort_order(trip.id, day_number)
                )
                item = TripItem(
                    trip_id=trip.id,
                    destination_id=destination.id,
                    destination=destination,
                    day_number=day_number,
                    visit_date=visit_date,
                    start_time=payload.start_time,
                    duration_minutes=payload.duration_minutes,
                    sort_order=sort_order,
                    notes=payload.notes,
                )
                try:
                    with self.session.begin_nested():
                        self.repository.add_trip_item(item)
                        self.repository.flush()
                except IntegrityError as exc:
                    if self._is_position_conflict(exc) and attempt + 1 < attempts:
                        continue
                    if self._is_position_conflict(exc):
                        raise TripConcurrentModificationError() from exc
                    raise TripPersistenceError() from exc
                self.session.commit()
                trip.version = next_version
                return self._item(item)
            raise TripConcurrentModificationError()

        return self._write(operation)

    def update_trip_item(
        self,
        user_id: int,
        trip_id: int,
        item_id: int,
        payload: TripItemUpdate,
    ) -> TripItemResponse:
        trip = self._owned_trip(user_id, trip_id)
        item = self._trip_item(trip.id, item_id)
        changes = payload.model_dump(exclude_unset=True)
        expected_version = changes.pop("expected_version", None) or trip.version
        destination_id = changes.get("destination_id", item.destination_id)
        destination = (
            self._public_destination(destination_id)
            if destination_id != item.destination_id
            else item.destination
        )
        if "day_number" in changes and "visit_date" not in changes:
            candidate_day = changes["day_number"]
            candidate_date = None
        elif "visit_date" in changes and "day_number" not in changes:
            candidate_day = None if changes["visit_date"] is not None else item.day_number
            candidate_date = changes["visit_date"]
        else:
            candidate_day = changes.get("day_number", item.day_number)
            candidate_date = changes.get("visit_date", item.visit_date)
        day_number, visit_date = self._resolve_item_date(
            trip,
            candidate_day,
            candidate_date,
        )
        candidate_start_time = changes.get("start_time", item.start_time)
        candidate_duration = changes.get("duration_minutes", item.duration_minutes)
        self._assert_no_time_conflict(
            trip.items,
            day_number,
            candidate_start_time,
            candidate_duration,
            exclude_item_id=item.id,
        )

        def operation() -> TripItemResponse:
            next_version = self._increment_version(
                trip,
                user_id,
                expected_version,
            )
            for field, value in changes.items():
                setattr(item, field, value)
            item.destination_id = destination_id
            item.destination = destination
            item.day_number = day_number
            item.visit_date = visit_date
            self.repository.flush()
            self.session.commit()
            trip.version = next_version
            return self._item(item)

        return self._write(operation)

    def delete_trip_item(
        self,
        user_id: int,
        trip_id: int,
        item_id: int,
        expected_version: int | None = None,
    ) -> None:
        trip = self._owned_trip(user_id, trip_id)
        item = self._trip_item(trip.id, item_id)
        current_version = expected_version or trip.version

        def operation() -> None:
            self._increment_version(trip, user_id, current_version)
            self.repository.delete_trip_item(item)
            self.repository.flush()
            self.session.commit()

        self._write(operation)

    def reorder_trip_items(
        self, user_id: int, trip_id: int, payload: TripItemReorderRequest
    ) -> TripDetailResponse:
        if len(payload.items) > MAX_TRIP_ITEMS:
            raise TripItemLimitExceededError()
        trip = self._owned_trip(user_id, trip_id)

        def operation() -> TripDetailResponse:
            items = list(self.repository.list_trip_items(trip.id))
            requested_ids = [entry.item_id for entry in payload.items]
            if len(requested_ids) != len(set(requested_ids)):
                raise InvalidTripItemOrderError()
            if set(requested_ids) != {item.id for item in items}:
                raise InvalidTripItemOrderError()
            by_id = {item.id: item for item in items}
            next_version = self.repository.increment_trip_version(
                trip.id,
                user_id,
                payload.expected_version,
            )
            if next_version is None:
                raise TripConcurrentModificationError()

            temporary_base = self.repository.max_sort_order(trip.id) + len(items) + 1
            for position, item in enumerate(items):
                item.sort_order = temporary_base + position
            self.repository.flush()

            day_positions: dict[int, int] = {}
            for entry in payload.items:
                self._validate_day(trip, entry.day_number)
                item = by_id[entry.item_id]
                item.day_number = entry.day_number
                item.visit_date = self._date_for_day(trip, entry.day_number)
                item.sort_order = day_positions.get(entry.day_number, 0)
                day_positions[entry.day_number] = item.sort_order + 1

            self._assert_no_time_conflicts(items)
            self.repository.flush()
            self.session.commit()
            trip.version = next_version
            trip.items = sorted(
                items,
                key=lambda item: (item.day_number, item.sort_order, item.id),
            )
            return self._detail(trip)

        return self._write(operation)

    def _increment_version(
        self,
        trip: Trip,
        user_id: int,
        expected_version: int,
    ) -> int:
        next_version = self.repository.increment_trip_version(
            trip.id,
            user_id,
            expected_version,
        )
        if next_version is None:
            raise TripConcurrentModificationError()
        return next_version

    def _owned_trip(self, user_id: int, trip_id: int) -> Trip:
        try:
            trip = self.repository.get_owned_trip_by_id(trip_id, user_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        if trip is None:
            raise TripNotFoundError()
        return trip

    def _trip_item(self, trip_id: int, item_id: int) -> TripItem:
        try:
            item = self.repository.get_trip_item_by_id(trip_id, item_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        if item is None:
            raise TripItemNotFoundError()
        return item

    def _public_destination(self, destination_id: int):
        try:
            destination = self.repository.get_public_destination(destination_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise TripPersistenceError() from exc
        if destination is None:
            raise DestinationUnavailableForTripError()
        return destination

    @staticmethod
    def _validate_status_transition(trip: Trip, new_status: TripStatus) -> None:
        current = trip.status

        if new_status == current:
            return

        allowed = {
            TripStatus.DRAFT: {
                TripStatus.PLANNED,
                TripStatus.CANCELLED,
            },
            TripStatus.PLANNED: {
                TripStatus.DRAFT,
                TripStatus.ACTIVE,
                TripStatus.CANCELLED,
            },
            TripStatus.ACTIVE: {
                TripStatus.COMPLETED,
                TripStatus.CANCELLED,
            },
            TripStatus.COMPLETED: {
                TripStatus.PLANNED,
            },
            TripStatus.CANCELLED: {
                TripStatus.DRAFT,
            },
        }

        if new_status not in allowed[current]:
            raise InvalidTripStatusTransitionError()

        if new_status == TripStatus.PLANNED and not trip.items:
            raise InvalidTripStatusTransitionError()

    @staticmethod
    def _validate_date_range(start_date: date | None, end_date: date | None) -> None:
        if start_date is not None and end_date is not None and end_date < start_date:
            raise InvalidTripDateRangeError()

    @classmethod
    def _validate_existing_items(
        cls, items: Sequence[TripItem], start_date: date | None, end_date: date | None
    ) -> None:
        temporary = Trip(start_date=start_date, end_date=end_date)
        for item in items:
            cls._validate_day(temporary, item.day_number)
            if item.visit_date is not None:
                cls._validate_visit_date(temporary, item.visit_date)
                if start_date is not None:
                    expected = (item.visit_date - start_date).days + 1
                    if expected != item.day_number:
                        raise TripItemDateOutOfRangeError()

    @classmethod
    def _resolve_item_date(
        cls, trip: Trip, day_number: int | None, visit_date: date | None
    ) -> tuple[int, date | None]:
        if visit_date is not None:
            cls._validate_visit_date(trip, visit_date)
            if trip.start_date is None:
                raise TripItemDateOutOfRangeError()
            derived_day = (visit_date - trip.start_date).days + 1
            if day_number is not None and day_number != derived_day:
                raise TripItemDateOutOfRangeError()
            day_number = derived_day
        day_number = day_number or 1
        cls._validate_day(trip, day_number)
        if visit_date is None:
            visit_date = cls._date_for_day(trip, day_number)
        return day_number, visit_date

    @staticmethod
    def _validate_day(trip: Trip, day_number: int) -> None:
        if day_number < 1:
            raise InvalidTripDayError()
        if trip.start_date is not None and trip.end_date is not None:
            if day_number > (trip.end_date - trip.start_date).days + 1:
                raise InvalidTripDayError()

    @staticmethod
    def _validate_visit_date(trip: Trip, visit_date: date) -> None:
        if trip.start_date is not None and visit_date < trip.start_date:
            raise TripItemDateOutOfRangeError()
        if trip.end_date is not None and visit_date > trip.end_date:
            raise TripItemDateOutOfRangeError()

    @staticmethod
    def _date_for_day(trip: Trip, day_number: int) -> date | None:
        if trip.start_date is None:
            return None
        from datetime import timedelta

        return trip.start_date + timedelta(days=day_number - 1)

    @staticmethod
    def _time_seconds(value: time) -> float:
        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
            + value.microsecond / 1_000_000
        )

    @classmethod
    def _assert_no_time_conflict(
        cls,
        items: Sequence[TripItem],
        day_number: int,
        start_time: time | None,
        duration_minutes: int | None,
        exclude_item_id: int | None = None,
    ) -> None:
        if start_time is None or duration_minutes is None:
            return

        candidate_start = cls._time_seconds(start_time)
        candidate_end = candidate_start + duration_minutes * 60

        for existing in items:
            if existing.day_number != day_number:
                continue
            if exclude_item_id is not None and existing.id == exclude_item_id:
                continue
            if existing.start_time is None or existing.duration_minutes is None:
                continue

            existing_start = cls._time_seconds(existing.start_time)
            existing_end = existing_start + existing.duration_minutes * 60

            if candidate_start < existing_end and existing_start < candidate_end:
                raise TripItemTimeConflictError()

    @classmethod
    def _assert_no_time_conflicts(cls, items: Sequence[TripItem]) -> None:
        for item in items:
            cls._assert_no_time_conflict(
                items,
                item.day_number,
                item.start_time,
                item.duration_minutes,
                exclude_item_id=item.id,
            )

    @staticmethod
    def _new_share_token() -> str:
        return secrets.token_urlsafe(32)

    def _write(self, operation):
        try:
            return operation()
        except IntegrityError as exc:
            self.session.rollback()
            if self._is_position_conflict(exc):
                raise TripConcurrentModificationError() from exc
            raise TripPersistenceError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise TripPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()

    @staticmethod
    def _constraint_name(error: IntegrityError) -> str | None:
        diagnostic = getattr(error.orig, "diag", None)
        return getattr(diagnostic, "constraint_name", None)

    @classmethod
    def _is_position_conflict(cls, error: IntegrityError) -> bool:
        name = cls._constraint_name(error)
        return name == "uq_trip_items_trip_day_position" or (
            name is None
            and "trip_items.trip_id, trip_items.day_number, trip_items.sort_order"
            in str(error.orig)
        )

    @classmethod
    def _item(cls, item: TripItem) -> TripItemResponse:
        translations = {
            entry.language_code.lower(): entry for entry in item.destination.translations
        }
        return TripItemResponse(
            id=item.id,
            destination=TripDestinationSummary(
                id=item.destination.id,
                slug=item.destination.slug,
                name_ar=cls._translation_name(translations.get("ar")),
                name_en=cls._translation_name(translations.get("en")),
                latitude=item.destination.latitude,
                longitude=item.destination.longitude,
            ),
            day_number=item.day_number,
            visit_date=item.visit_date,
            start_time=item.start_time,
            duration_minutes=item.duration_minutes,
            sort_order=item.sort_order,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _translation_name(translation: DestinationTranslation | None) -> str | None:
        return translation.name if translation is not None else None

    @staticmethod
    def _duration_days(trip: Trip) -> int | None:
        if trip.start_date is None or trip.end_date is None:
            return None
        return (trip.end_date - trip.start_date).days + 1

    @classmethod
    def _summary(cls, trip: Trip, item_count: int | None = None) -> TripSummaryResponse:
        return TripSummaryResponse(
            id=trip.id,
            title=trip.title,
            description=trip.description,
            start_date=trip.start_date,
            end_date=trip.end_date,
            status=trip.status,
            visibility=trip.visibility,
            version=trip.version,
            duration_days=cls._duration_days(trip),
            item_count=len(trip.items) if item_count is None else item_count,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )

    @classmethod
    def _detail(cls, trip: Trip) -> TripDetailResponse:
        summary = cls._summary(trip)
        return TripDetailResponse(
            **summary.model_dump(),
            items=[cls._item(item) for item in trip.items],
        )

    @classmethod
    def _owner_detail(cls, trip: Trip) -> TripOwnerDetailResponse:
        detail = cls._detail(trip)
        return TripOwnerDetailResponse(
            **detail.model_dump(),
            share_token=trip.share_token,
        )
