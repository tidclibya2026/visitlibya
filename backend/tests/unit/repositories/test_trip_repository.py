from unittest.mock import MagicMock

from app.models.destination import DestinationStatus
from app.models.trip import Trip
from app.models.trip_item import TripItem
from app.repositories.trip import TripListEntry, TripRepository


def test_trip_model_constraints_relationships_and_cascades() -> None:
    trip_fk = next(iter(Trip.__table__.c.user_id.foreign_keys))
    item_trip_fk = next(iter(TripItem.__table__.c.trip_id.foreign_keys))
    item_destination_fk = next(iter(TripItem.__table__.c.destination_id.foreign_keys))
    assert trip_fk.ondelete == "CASCADE"
    assert item_trip_fk.ondelete == "CASCADE"
    assert item_destination_fk.ondelete == "CASCADE"
    assert Trip.user.property.mapper.class_.trips.property.passive_deletes is True
    assert Trip.items.property.passive_deletes is True
    assert TripItem.destination.property.mapper.class_.trip_items.property.passive_deletes is True
    assert any(
        constraint.name == "uq_trip_items_trip_destination_day"
        for constraint in TripItem.__table__.constraints
    )
    assert any(
        constraint.name == "uq_trip_items_trip_day_position"
        for constraint in TripItem.__table__.constraints
    )
    assert Trip.__table__.c.version.server_default is not None


def test_trip_queries_are_owned_paginated_and_deterministic() -> None:
    session = MagicMock()
    session.scalar.side_effect = [MagicMock(), 3]
    listed_trip = MagicMock()
    session.execute.return_value.all.return_value = [(listed_trip, 4)]
    repository = TripRepository(session)

    assert repository.get_owned_trip_by_id(7, 2) is not None
    assert repository.list_user_trips(2, 5, 10) == [TripListEntry(listed_trip, 4)]
    assert repository.count_user_trips(2) == 3

    owned_sql = str(session.scalar.call_args_list[0].args[0])
    list_statement = session.execute.call_args.args[0]
    list_sql = str(list_statement)
    count_sql = str(session.scalar.call_args_list[1].args[0])
    assert "trips.id" in owned_sql and "trips.user_id" in owned_sql
    assert "trips.created_at DESC" in list_sql and "trips.id DESC" in list_sql
    assert "LIMIT" in list_sql and "OFFSET" in list_sql
    assert "SELECT count(trip_items.id)" in list_sql
    assert "JOIN trip_items" not in list_sql
    assert "trips.user_id" in count_sql


def test_item_queries_duplicate_destination_and_next_order() -> None:
    session = MagicMock()
    session.scalar.side_effect = [MagicMock(), MagicMock(), MagicMock(), 4]
    session.scalars.return_value.all.return_value = [MagicMock()]
    repository = TripRepository(session)

    assert repository.get_trip_item_by_id(1, 2) is not None
    assert repository.list_trip_items(1)
    assert repository.find_duplicate_trip_item(1, 7, 2, exclude_item_id=9)
    assert repository.get_public_destination(7)
    assert repository.next_sort_order(1, 2) == 5

    duplicate_sql = str(session.scalar.call_args_list[1].args[0])
    destination_statement = session.scalar.call_args_list[2].args[0]
    destination_sql = str(destination_statement)
    assert "trip_items.id !=" in duplicate_sql
    assert "destinations.status" in destination_sql
    assert DestinationStatus.PUBLISHED in destination_statement.compile().params.values()


def test_repository_write_methods_never_commit_or_rollback() -> None:
    session = MagicMock()
    repository = TripRepository(session)
    trip = Trip(user_id=1, title="Libya")
    item = TripItem(trip_id=1, destination_id=2, day_number=1)
    repository.create_trip(trip)
    repository.add_trip_item(item)
    repository.flush()
    repository.delete_trip_item(item)
    repository.delete_trip(trip)
    assert session.add.call_count == 2
    assert session.delete.call_count == 2
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_item_count_max_order_and_optimistic_version_queries() -> None:
    session = MagicMock()
    session.scalar.side_effect = [0, 9, 3]
    repository = TripRepository(session)

    assert repository.count_trip_items(3) == 0
    assert repository.max_sort_order(3) == 9
    assert repository.increment_trip_version(3, 1, 2) == 3

    count_sql = str(session.scalar.call_args_list[0].args[0])
    max_sql = str(session.scalar.call_args_list[1].args[0])
    version_sql = str(session.scalar.call_args_list[2].args[0])
    assert "count(trip_items.id)" in count_sql and "trip_items.trip_id" in count_sql
    assert "max(trip_items.sort_order)" in max_sql
    assert "trips.user_id" in version_sql and "trips.version" in version_sql
    assert "RETURNING trips.version" in version_sql
