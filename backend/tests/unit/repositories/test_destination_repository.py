from unittest.mock import MagicMock

from app.models.destination import Destination, DestinationStatus
from app.repositories.destination import DestinationRepository


def test_slug_exists_supports_excluding_destination() -> None:
    session = MagicMock()
    session.scalar.side_effect = [1, None]
    repository = DestinationRepository(session)

    assert repository.slug_exists("leptis-magna") is True
    assert repository.slug_exists("leptis-magna", exclude_destination_id=1) is False
    assert session.scalar.call_count == 2


def test_category_exists() -> None:
    session = MagicMock()
    session.scalar.side_effect = [7, None]
    repository = DestinationRepository(session)

    assert repository.category_exists(7) is True
    assert repository.category_exists(99) is False


def test_public_slug_lookup_requires_published_and_active() -> None:
    session = MagicMock()
    repository = DestinationRepository(session)

    repository.get_public_by_slug("leptis-magna")

    statement = str(session.scalar.call_args.args[0])
    assert "destinations.slug" in statement
    assert "destinations.status" in statement
    assert "destinations.is_active" in statement


def test_list_and_count_use_the_same_filters() -> None:
    destination = Destination(id=1, slug="leptis-magna")
    scalar_result = MagicMock()
    scalar_result.all.return_value = [destination]
    session = MagicMock()
    session.scalars.return_value = scalar_result
    session.scalar.return_value = 1
    repository = DestinationRepository(session)

    filters = {
        "status": DestinationStatus.PUBLISHED,
        "category_id": 3,
        "region": "Tripolitania",
        "municipality": "Khoms",
        "is_featured": True,
        "is_active": True,
    }
    items = repository.list(skip=0, limit=20, **filters)
    total = repository.count(**filters)

    assert list(items) == [destination]
    assert total == 1
    list_sql = str(session.scalars.call_args.args[0])
    count_sql = str(session.scalar.call_args.args[0])
    for column in (
        "status",
        "category_id",
        "region",
        "municipality",
        "is_featured",
        "is_active",
    ):
        assert column in list_sql
        assert column in count_sql
    assert "LIMIT" in list_sql
    assert "OFFSET" in list_sql


def test_repository_write_helpers_do_not_manage_transactions() -> None:
    session = MagicMock()
    repository = DestinationRepository(session)
    destination = Destination(slug="leptis-magna")

    repository.add(destination)
    repository.flush()
    repository.refresh(destination)
    repository.delete(destination)

    session.add.assert_called_once_with(destination)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(
        destination,
        attribute_names=["category", "translations"],
    )
    session.delete.assert_called_once_with(destination)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()

def test_public_bbox_query_requires_governed_spatial_destination() -> None:
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session = MagicMock()
    session.scalars.return_value = scalar_result
    repository = DestinationRepository(session)

    repository.list_public_in_bbox(
        min_longitude=12.0,
        min_latitude=22.0,
        max_longitude=25.0,
        max_latitude=34.0,
        skip=0,
        limit=100,
    )

    statement = str(session.scalars.call_args.args[0])

    assert "ST_Intersects" in statement
    assert "ST_MakeEnvelope" in statement
    assert "destinations.geometry IS NOT NULL" in statement
    assert "destinations.status" in statement
    assert "destinations.is_active" in statement
    assert "LIMIT" in statement
    assert "OFFSET" in statement


def test_public_bbox_count_uses_same_spatial_governance() -> None:
    session = MagicMock()
    session.scalar.return_value = 4
    repository = DestinationRepository(session)

    total = repository.count_public_in_bbox(
        min_longitude=12.0,
        min_latitude=22.0,
        max_longitude=25.0,
        max_latitude=34.0,
    )

    assert total == 4

    statement = str(session.scalar.call_args.args[0])

    assert "count(destinations.id)" in statement
    assert "ST_Intersects" in statement
    assert "ST_MakeEnvelope" in statement
    assert "destinations.geometry IS NOT NULL" in statement
    assert "destinations.status" in statement
    assert "destinations.is_active" in statement


def test_public_nearby_query_uses_geography_meter_distance() -> None:
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session = MagicMock()
    session.scalars.return_value = scalar_result
    repository = DestinationRepository(session)

    repository.list_public_nearby(
        longitude=13.1913,
        latitude=32.8872,
        radius_meters=5000,
        limit=20,
    )

    statement = str(session.scalars.call_args.args[0])

    assert "ST_DWithin" in statement
    assert "ST_MakePoint" in statement
    assert "ST_SetSRID" in statement
    assert "ST_Distance" in statement
    assert "geography" in statement.lower()
    assert "destinations.geometry IS NOT NULL" in statement
    assert "destinations.status" in statement
    assert "destinations.is_active" in statement
    assert "ORDER BY" in statement
    assert "LIMIT" in statement


def test_public_spatial_repository_does_not_manage_transactions() -> None:
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session = MagicMock()
    session.scalars.return_value = scalar_result
    session.scalar.return_value = 0
    repository = DestinationRepository(session)

    repository.list_public_in_bbox(
        min_longitude=12.0,
        min_latitude=22.0,
        max_longitude=25.0,
        max_latitude=34.0,
        skip=0,
        limit=50,
    )
    repository.count_public_in_bbox(
        min_longitude=12.0,
        min_latitude=22.0,
        max_longitude=25.0,
        max_latitude=34.0,
    )
    repository.list_public_nearby(
        longitude=13.1913,
        latitude=32.8872,
        radius_meters=10000,
        limit=20,
    )

    session.commit.assert_not_called()
    session.rollback.assert_not_called()
