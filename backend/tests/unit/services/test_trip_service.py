from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    DestinationUnavailableForTripError,
    DuplicateTripDestinationError,
    InvalidTripDateRangeError,
    InvalidTripDayError,
    InvalidTripItemOrderError,
    TripConcurrentModificationError,
    TripItemDateOutOfRangeError,
    TripItemLimitExceededError,
    TripItemNotFoundError,
    TripNotFoundError,
    TripPersistenceError,
)
from app.core.trip_constants import (
    MAX_TRIP_DESCRIPTION_LENGTH,
    MAX_TRIP_ITEM_NOTES_LENGTH,
    MAX_TRIP_ITEMS,
)
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.models.trip import Trip, TripStatus, TripVisibility
from app.models.trip_item import TripItem
from app.repositories.trip import TripListEntry
from app.schemas.trip import (
    TripCreate,
    TripItemCreate,
    TripItemReorderElement,
    TripItemReorderRequest,
    TripItemUpdate,
    TripUpdate,
)
from app.services.trip import TripService


NOW = datetime.now(UTC)


class ConstraintViolation(Exception):
    def __init__(self, constraint_name: str) -> None:
        self.diag = type("Diagnostic", (), {"constraint_name": constraint_name})()
        super().__init__(constraint_name)


def destination(destination_id: int = 7, published: bool = True) -> Destination:
    value = Destination(
        id=destination_id,
        slug=f"destination-{destination_id}",
        status=DestinationStatus.PUBLISHED if published else DestinationStatus.DRAFT,
        is_active=published,
        created_at=NOW,
        updated_at=NOW,
    )
    value.translations = [
        DestinationTranslation(
            id=destination_id,
            destination_id=destination_id,
            language_code="en",
            name=f"Destination {destination_id}",
            created_at=NOW,
            updated_at=NOW,
        )
    ]
    return value


def trip(items: list[TripItem] | None = None) -> Trip:
    value = Trip(
        id=3,
        user_id=1,
        title="Coastal Journey",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
        status=TripStatus.DRAFT,
        visibility=TripVisibility.PRIVATE,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )
    value.items = items or []
    return value


def item(item_id: int = 11, day: int = 1, destination_id: int = 7) -> TripItem:
    return TripItem(
        id=item_id,
        trip_id=3,
        destination_id=destination_id,
        destination=destination(destination_id),
        day_number=day,
        visit_date=date(2026, 9, day),
        sort_order=0,
        created_at=NOW,
        updated_at=NOW,
    )


def service():
    session = MagicMock()
    session.is_active = True
    repository = MagicMock()
    repository.increment_trip_version.side_effect = (
        lambda trip_id, user_id, expected_version: expected_version + 1
    )
    return TripService(session, repository), session, repository


def test_create_list_get_update_and_delete_trip() -> None:
    subject, session, repository = service()

    def assign_trip() -> None:
        created = repository.create_trip.call_args.args[0]
        created.id = 3
        created.version = 1
        created.created_at = created.updated_at = NOW
        created.items = []

    repository.flush.side_effect = assign_trip
    created = subject.create_trip(
        1,
        TripCreate(
            title="  Coastal Journey  ",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 3),
        ),
    )
    assert created.title == "Coastal Journey"
    session.commit.assert_called_once()

    value = trip()
    repository.list_user_trips.return_value = [TripListEntry(value, 0)]
    repository.count_user_trips.return_value = 1
    listed = subject.list_user_trips(1, 0, 20)
    assert listed.total == 1 and listed.items[0].duration_days == 3

    repository.get_owned_trip_by_id.return_value = value
    assert subject.get_trip(1, 3).id == 3
    repository.flush.side_effect = None
    updated = subject.update_trip(1, 3, TripUpdate(title="New title"))
    assert updated.title == "New title"
    subject.delete_trip(1, 3)
    repository.delete_trip.assert_called_once_with(value)


def test_invalid_date_range_and_date_update_invalidating_items() -> None:
    subject, _, repository = service()
    with pytest.raises(InvalidTripDateRangeError):
        subject.create_trip(
            1,
            TripCreate(start_date=date(2026, 9, 3), end_date=date(2026, 9, 1), title="Bad"),
        )
    value = trip([item(day=3)])
    repository.get_owned_trip_by_id.return_value = value
    with pytest.raises(InvalidTripDayError):
        subject.update_trip(1, 3, TripUpdate(end_date=date(2026, 9, 2)))


def test_metadata_update_uses_expected_version_and_rejects_stale_write() -> None:
    subject, session, repository = service()
    value = trip()
    repository.get_owned_trip_by_id.return_value = value
    repository.increment_trip_version.side_effect = [2, None]

    updated = subject.update_trip(
        1,
        3,
        TripUpdate(title="First writer", expected_version=1),
    )

    assert updated.version == 2
    assert updated.title == "First writer"
    repository.increment_trip_version.assert_called_with(3, 1, 1)
    value.title = "First writer"
    value.version = 2
    with pytest.raises(TripConcurrentModificationError):
        subject.update_trip(
            1,
            3,
            TripUpdate(title="Stale writer", expected_version=1),
        )
    assert value.title == "First writer"
    assert session.rollback.call_count == 1


def test_ownership_is_hidden_as_not_found() -> None:
    subject, _, repository = service()
    repository.get_owned_trip_by_id.return_value = None
    with pytest.raises(TripNotFoundError):
        subject.get_trip(2, 3)


def test_add_item_derives_date_and_order() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.next_sort_order.return_value = 2

    def assign_item() -> None:
        created = repository.add_trip_item.call_args.args[0]
        created.id = 11
        created.created_at = created.updated_at = NOW

    repository.flush.side_effect = assign_item
    result = subject.add_trip_item(1, 3, TripItemCreate(destination_id=7, day_number=2))
    assert result.visit_date == date(2026, 9, 2)
    assert result.sort_order == 2
    session.commit.assert_called_once()


def test_add_item_rejects_unavailable_invalid_and_duplicate() -> None:
    subject, _, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.return_value = None
    with pytest.raises(DestinationUnavailableForTripError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))

    repository.get_public_destination.return_value = destination()
    with pytest.raises(InvalidTripDayError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7, day_number=4))
    with pytest.raises(TripItemDateOutOfRangeError):
        subject.add_trip_item(
            1,
            3,
            TripItemCreate(destination_id=7, day_number=1, visit_date=date(2026, 9, 2)),
        )
    repository.find_duplicate_trip_item.return_value = item()
    with pytest.raises(DuplicateTripDestinationError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7, day_number=1))


def test_update_and_delete_item_are_owned() -> None:
    subject, _, repository = service()
    value = trip()
    current = item()
    repository.get_owned_trip_by_id.return_value = value
    repository.get_trip_item_by_id.return_value = current
    repository.find_duplicate_trip_item.return_value = None
    result = subject.update_trip_item(1, 3, 11, TripItemUpdate(day_number=2, notes="Museum"))
    assert result.day_number == 2 and result.notes == "Museum"
    subject.delete_trip_item(1, 3, 11)
    repository.delete_trip_item.assert_called_once_with(current)
    repository.get_trip_item_by_id.return_value = None
    with pytest.raises(TripItemNotFoundError):
        subject.delete_trip_item(1, 3, 99)


def test_item_mutations_use_the_client_expected_version() -> None:
    subject, _, repository = service()
    value = trip()
    current = item()
    repository.get_owned_trip_by_id.return_value = value
    repository.get_trip_item_by_id.return_value = current
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.count_trip_items.return_value = 0
    repository.next_sort_order.return_value = 0

    def assign_item() -> None:
        created = repository.add_trip_item.call_args.args[0]
        created.id = 15
        created.created_at = created.updated_at = NOW

    repository.flush.side_effect = assign_item
    subject.add_trip_item(
        1,
        3,
        TripItemCreate(
            destination_id=7,
            expected_version=4,
        ),
    )
    repository.increment_trip_version.assert_called_with(3, 1, 4)

    repository.flush.side_effect = None
    subject.update_trip_item(
        1,
        3,
        11,
        TripItemUpdate(notes="Updated", expected_version=5),
    )
    repository.increment_trip_version.assert_called_with(3, 1, 5)

    subject.delete_trip_item(1, 3, 11, expected_version=6)
    repository.increment_trip_version.assert_called_with(3, 1, 6)


def test_stale_item_mutation_rolls_back_without_applying_changes() -> None:
    subject, session, repository = service()
    current = item()
    original_notes = current.notes
    repository.get_owned_trip_by_id.return_value = trip([current])
    repository.get_trip_item_by_id.return_value = current
    repository.find_duplicate_trip_item.return_value = None
    repository.increment_trip_version.side_effect = None
    repository.increment_trip_version.return_value = None

    with pytest.raises(TripConcurrentModificationError):
        subject.update_trip_item(
            1,
            3,
            11,
            TripItemUpdate(notes="Stale", expected_version=1),
        )

    assert current.notes == original_notes
    repository.flush.assert_not_called()
    session.rollback.assert_called_once_with()


def test_reorder_is_atomic_normalized_and_rejects_invalid_sets() -> None:
    subject, session, repository = service()
    first, second = item(11, 1, 7), item(12, 2, 8)
    repository.get_owned_trip_by_id.return_value = trip([first, second])
    repository.list_trip_items.return_value = [first, second]
    payload = TripItemReorderRequest(
        expected_version=1,
        items=[
            TripItemReorderElement(item_id=12, day_number=1),
            TripItemReorderElement(item_id=11, day_number=1),
        ]
    )
    repository.increment_trip_version.side_effect = None
    repository.increment_trip_version.return_value = 2
    repository.max_sort_order.return_value = 1
    result = subject.reorder_trip_items(1, 3, payload)
    assert [entry.id for entry in result.items] == [12, 11]
    assert [entry.sort_order for entry in result.items] == [0, 1]
    assert result.version == 2
    session.commit.assert_called_once()

    duplicate = TripItemReorderRequest(
        expected_version=2,
        items=[
            TripItemReorderElement(item_id=11, day_number=1),
            TripItemReorderElement(item_id=11, day_number=2),
        ]
    )
    with pytest.raises(InvalidTripItemOrderError):
        subject.reorder_trip_items(1, 3, duplicate)


@pytest.mark.parametrize("error", [IntegrityError("x", {}, Exception()), SQLAlchemyError("x")])
def test_writes_rollback_on_persistence_failure(error) -> None:
    subject, session, repository = service()
    repository.flush.side_effect = error
    payload = TripCreate(title="Safe")
    expected = TripPersistenceError
    with pytest.raises(expected):
        subject.create_trip(1, payload)
    session.rollback.assert_called_once()


def test_duplicate_constraint_maps_to_domain_conflict() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.next_sort_order.return_value = 0
    repository.flush.side_effect = IntegrityError(
        "x",
        {},
        ConstraintViolation("uq_trip_items_trip_destination_day"),
    )
    with pytest.raises(DuplicateTripDestinationError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))
    session.rollback.assert_called_once()


def test_position_conflict_retries_with_a_new_candidate() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.next_sort_order.side_effect = [0, 1]

    position_conflict = IntegrityError(
        "x",
        {},
        ConstraintViolation("uq_trip_items_trip_day_position"),
    )

    flush_attempt = 0

    def flush_with_one_conflict() -> None:
        nonlocal flush_attempt
        flush_attempt += 1
        if flush_attempt == 1:
            raise position_conflict
        created = repository.add_trip_item.call_args.args[0]
        created.id = 12
        created.created_at = created.updated_at = NOW

    repository.flush.side_effect = flush_with_one_conflict
    result = subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))

    assert result.sort_order == 1
    assert repository.next_sort_order.call_count == 2
    assert repository.flush.call_count == 2
    session.commit.assert_called_once()


def test_position_retry_exhaustion_and_unknown_integrity_are_safe() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.next_sort_order.side_effect = [0, 1, 2]
    repository.flush.side_effect = IntegrityError(
        "x",
        {},
        ConstraintViolation("uq_trip_items_trip_day_position"),
    )

    with pytest.raises(TripConcurrentModificationError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))
    assert repository.flush.call_count == 3
    session.rollback.assert_called_once()

    repository.flush.reset_mock()
    repository.next_sort_order.side_effect = None
    repository.next_sort_order.return_value = 3
    repository.flush.side_effect = IntegrityError("x", {}, Exception("unknown"))
    with pytest.raises(TripPersistenceError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=8))
    assert session.rollback.call_count == 2


def test_read_failure_is_generic() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.side_effect = SQLAlchemyError("down")
    session.is_active = False
    with pytest.raises(TripPersistenceError):
        subject.get_trip(1, 3)
    session.rollback.assert_called_once()


def test_list_and_item_reads_map_database_failures() -> None:
    subject, session, repository = service()
    repository.list_user_trips.side_effect = SQLAlchemyError("down")
    session.is_active = False
    with pytest.raises(TripPersistenceError):
        subject.list_user_trips(1, 0, 20)
    repository.get_owned_trip_by_id.side_effect = None
    repository.get_owned_trip_by_id.return_value = trip()
    repository.get_trip_item_by_id.side_effect = SQLAlchemyError("down")
    with pytest.raises(TripPersistenceError):
        subject.delete_trip_item(1, 3, 11)
    assert session.rollback.call_count == 2


def test_update_item_destination_and_duplicate_detection() -> None:
    subject, _, repository = service()
    current = item()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.get_trip_item_by_id.return_value = current
    repository.get_public_destination.return_value = destination(8)
    repository.find_duplicate_trip_item.return_value = None
    result = subject.update_trip_item(
        1, 3, 11, TripItemUpdate(destination_id=8, visit_date=date(2026, 9, 2))
    )
    assert result.destination.id == 8 and result.day_number == 2

    repository.find_duplicate_trip_item.return_value = item(12, 2, 8)
    with pytest.raises(DuplicateTripDestinationError):
        subject.update_trip_item(1, 3, 11, TripItemUpdate(day_number=2))


def test_reorder_rejects_foreign_items_invalid_days_and_new_duplicates() -> None:
    subject, _, repository = service()
    first, second = item(11, 1, 7), item(12, 2, 8)
    repository.get_owned_trip_by_id.return_value = trip([first, second])
    repository.list_trip_items.return_value = [first, second]
    missing = TripItemReorderRequest(
        expected_version=1,
        items=[TripItemReorderElement(item_id=11, day_number=1)]
    )
    with pytest.raises(InvalidTripItemOrderError):
        subject.reorder_trip_items(1, 3, missing)

    invalid_day = TripItemReorderRequest(
        expected_version=1,
        items=[
            TripItemReorderElement(item_id=11, day_number=4),
            TripItemReorderElement(item_id=12, day_number=1),
        ]
    )
    with pytest.raises(InvalidTripDayError):
        subject.reorder_trip_items(1, 3, invalid_day)

    second.destination_id = 7
    duplicate = TripItemReorderRequest(
        expected_version=1,
        items=[
            TripItemReorderElement(item_id=11, day_number=1),
            TripItemReorderElement(item_id=12, day_number=1),
        ]
    )
    with pytest.raises(DuplicateTripDestinationError):
        subject.reorder_trip_items(1, 3, duplicate)


def test_reorder_list_failure_is_generic_and_rolls_back() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.list_trip_items.side_effect = SQLAlchemyError("down")
    payload = TripItemReorderRequest(
        expected_version=1,
        items=[TripItemReorderElement(item_id=11, day_number=1)]
    )

    with pytest.raises(TripPersistenceError):
        subject.reorder_trip_items(1, 3, payload)

    session.rollback.assert_called_once()


def test_reorder_domain_error_is_preserved() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.list_trip_items.return_value = [item(11)]
    payload = TripItemReorderRequest(
        expected_version=1,
        items=[
            TripItemReorderElement(item_id=11, day_number=1),
            TripItemReorderElement(item_id=11, day_number=2),
        ]
    )

    with pytest.raises(InvalidTripItemOrderError):
        subject.reorder_trip_items(1, 3, payload)

    session.rollback.assert_called_once()


def test_trip_item_limit_allows_99_and_rejects_100() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.get_public_destination.return_value = destination()
    repository.find_duplicate_trip_item.return_value = None
    repository.next_sort_order.return_value = 99
    repository.count_trip_items.return_value = 99

    def assign_item() -> None:
        created = repository.add_trip_item.call_args.args[0]
        created.id = 111
        created.created_at = created.updated_at = NOW

    repository.flush.side_effect = assign_item
    result = subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))
    assert result.id == 111
    session.commit.assert_called_once()

    repository.count_trip_items.return_value = 100
    with pytest.raises(TripItemLimitExceededError):
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=8))


def test_text_and_reorder_schema_limits() -> None:
    assert len(TripCreate(title="Trip", description="x" * MAX_TRIP_DESCRIPTION_LENGTH).description) == 5_000
    assert len(TripUpdate(description="x" * MAX_TRIP_DESCRIPTION_LENGTH).description) == 5_000
    assert len(TripItemCreate(destination_id=1, notes="x" * MAX_TRIP_ITEM_NOTES_LENGTH).notes) == 2_000
    assert len(TripItemUpdate(notes="x" * MAX_TRIP_ITEM_NOTES_LENGTH).notes) == 2_000

    with pytest.raises(ValidationError):
        TripCreate(title="Trip", description="x" * (MAX_TRIP_DESCRIPTION_LENGTH + 1))
    with pytest.raises(ValidationError):
        TripUpdate(description="x" * (MAX_TRIP_DESCRIPTION_LENGTH + 1))
    with pytest.raises(ValidationError):
        TripItemCreate(destination_id=1, notes="x" * (MAX_TRIP_ITEM_NOTES_LENGTH + 1))
    with pytest.raises(ValidationError):
        TripItemUpdate(notes="x" * (MAX_TRIP_ITEM_NOTES_LENGTH + 1))

    valid_items = [
        TripItemReorderElement(item_id=index + 1, day_number=1)
        for index in range(MAX_TRIP_ITEMS)
    ]
    assert len(TripItemReorderRequest(expected_version=1, items=valid_items).items) == 100
    with pytest.raises(ValidationError):
        TripItemReorderRequest(
            expected_version=1,
            items=valid_items + [TripItemReorderElement(item_id=101, day_number=1)],
        )


def test_stale_reorder_rolls_back_before_item_mutation() -> None:
    subject, session, repository = service()
    current = item(11, 1, 7)
    repository.get_owned_trip_by_id.return_value = trip([current])
    repository.list_trip_items.return_value = [current]
    repository.increment_trip_version.side_effect = None
    repository.increment_trip_version.return_value = None
    payload = TripItemReorderRequest(
        expected_version=1,
        items=[TripItemReorderElement(item_id=11, day_number=2)],
    )

    with pytest.raises(TripConcurrentModificationError):
        subject.reorder_trip_items(1, 3, payload)

    assert current.day_number == 1
    assert current.sort_order == 0
    repository.flush.assert_not_called()
    session.rollback.assert_called_once()


def test_service_defensively_rejects_oversized_constructed_reorder() -> None:
    subject, _, repository = service()
    payload = TripItemReorderRequest.model_construct(
        expected_version=1,
        items=[
            TripItemReorderElement(item_id=index + 1, day_number=1)
            for index in range(MAX_TRIP_ITEMS + 1)
        ],
    )
    with pytest.raises(TripItemLimitExceededError):
        subject.reorder_trip_items(1, 3, payload)
    repository.get_owned_trip_by_id.assert_not_called()


def test_destination_read_failure_is_converted_without_database_details() -> None:
    subject, session, repository = service()
    repository.get_owned_trip_by_id.return_value = trip()
    repository.count_trip_items.return_value = 0
    repository.get_public_destination.side_effect = SQLAlchemyError("secret database detail")
    session.is_active = False

    with pytest.raises(TripPersistenceError) as raised:
        subject.add_trip_item(1, 3, TripItemCreate(destination_id=7))
    assert str(raised.value) == "Trip request could not be completed"
    session.rollback.assert_called()


def test_same_reorder_version_only_succeeds_once() -> None:
    subject, session, repository = service()
    current = item(11, 1, 7)
    value = trip([current])
    repository.get_owned_trip_by_id.return_value = value
    repository.list_trip_items.return_value = [current]
    repository.increment_trip_version.side_effect = [2, None]
    repository.max_sort_order.return_value = 0
    payload = TripItemReorderRequest(
        expected_version=1,
        items=[TripItemReorderElement(item_id=11, day_number=1)],
    )

    first = subject.reorder_trip_items(1, 3, payload)
    assert first.version == 2
    with pytest.raises(TripConcurrentModificationError):
        subject.reorder_trip_items(1, 3, payload)
    assert session.commit.call_count == 1
    assert session.rollback.call_count == 1
