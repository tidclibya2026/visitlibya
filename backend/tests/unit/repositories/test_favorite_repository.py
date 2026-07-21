from unittest.mock import MagicMock

from app.models.destination import DestinationStatus
from app.models.favorite import Favorite
from app.repositories.favorite import FavoriteRepository


def test_favorite_model_constraints_and_cascades() -> None:
    table = Favorite.__table__
    unique = next(item for item in table.constraints if item.name == "uq_favorites_user_destination")
    assert [column.name for column in unique.columns] == ["user_id", "destination_id"]
    assert next(iter(table.c.user_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.destination_id.foreign_keys)).ondelete == "CASCADE"
    assert Favorite.user.property.passive_deletes is False
    assert Favorite.destination.property.passive_deletes is False
    assert Favorite.user.property.mapper.class_.favorites.property.passive_deletes is True
    assert Favorite.destination.property.mapper.class_.favorites.property.passive_deletes is True


def test_get_favorite_and_public_destination() -> None:
    session = MagicMock()
    favorite = MagicMock()
    destination = MagicMock()
    session.scalar.side_effect = [favorite, destination]
    repository = FavoriteRepository(session)

    assert repository.get_by_user_and_destination(1, 7) is favorite
    favorite_sql = str(session.scalar.call_args_list[0].args[0])
    assert "favorites.user_id" in favorite_sql
    assert "favorites.destination_id" in favorite_sql

    assert repository.get_public_destination(7) is destination
    destination_sql = str(session.scalar.call_args_list[1].args[0])
    assert "destinations.status" in destination_sql
    destination_params = session.scalar.call_args_list[1].args[0].compile().params
    assert DestinationStatus.PUBLISHED in destination_params.values()
    assert "destinations.is_active" in destination_sql


def test_list_and_count_are_filtered_and_paginated() -> None:
    session = MagicMock()
    session.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
    session.scalar.return_value = 2
    repository = FavoriteRepository(session)

    items = repository.list_by_user(user_id=3, skip=5, limit=10)
    total = repository.count_by_user(3)

    assert len(items) == 2
    assert total == 2
    list_sql = str(session.scalars.call_args.args[0])
    count_sql = str(session.scalar.call_args.args[0])
    for sql in (list_sql, count_sql):
        assert "favorites.user_id" in sql
        assert "destinations.status" in sql
        assert "destinations.is_active" in sql
    assert "LIMIT" in list_sql and "OFFSET" in list_sql
    assert "favorites.created_at DESC" in list_sql
    assert "favorites.id DESC" in list_sql


def test_repository_write_helpers_do_not_commit() -> None:
    session = MagicMock()
    repository = FavoriteRepository(session)
    favorite = Favorite(user_id=1, destination_id=2)
    repository.add(favorite)
    repository.flush()
    repository.delete(favorite)
    session.add.assert_called_once_with(favorite)
    session.flush.assert_called_once()
    session.delete.assert_called_once_with(favorite)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
