from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    DestinationNotFoundError,
    FavoriteIntegrityError,
    FavoritePersistenceError,
)
from app.models.category import Category
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.models.favorite import Favorite
from app.models.media import DestinationMedia, MediaAsset
from app.services.favorite import FavoriteService


def make_destination(destination_id: int = 7) -> Destination:
    now = datetime.now(UTC)
    destination = Destination(
        id=destination_id,
        slug="leptis-magna",
        status=DestinationStatus.PUBLISHED,
        municipality="Al Khums",
        region="Tripolitania",
        is_featured=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    destination.category = Category(
        id=2,
        code="heritage",
        name_ar="تراث",
        name_en="Heritage",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    destination.translations = [
        DestinationTranslation(
            id=1,
            destination_id=destination_id,
            language_code="en",
            name="Leptis Magna",
            created_at=now,
            updated_at=now,
        )
    ]
    destination.media_items = []
    return destination


def make_favorite(destination: Destination | None = None) -> Favorite:
    return Favorite(
        id=11,
        user_id=1,
        destination_id=7,
        destination=destination or make_destination(),
        created_at=datetime.now(UTC),
    )


def make_service():
    session = MagicMock()
    session.is_active = True
    repository = MagicMock()
    return FavoriteService(session, repository), session, repository


def test_add_favorite_creates_and_commits() -> None:
    service, session, repository = make_service()
    repository.get_public_destination.return_value = make_destination()
    repository.get_by_user_and_destination.return_value = None
    def assign_database_values() -> None:
        favorite = repository.add.call_args.args[0]
        favorite.id = 11
        favorite.created_at = datetime.now(UTC)
    repository.flush.side_effect = assign_database_values
    result = service.add_favorite(1, 7)
    repository.add.assert_called_once()
    repository.flush.assert_called_once()
    session.commit.assert_called_once()
    assert result.destination.id == 7


def test_add_favorite_is_idempotent() -> None:
    service, session, repository = make_service()
    favorite = make_favorite()
    repository.get_public_destination.return_value = favorite.destination
    repository.get_by_user_and_destination.return_value = favorite
    first = service.add_favorite(1, 7)
    second = service.add_favorite(1, 7)
    assert first == second
    repository.add.assert_not_called()
    session.commit.assert_not_called()


def test_add_rejects_non_public_destination() -> None:
    service, session, repository = make_service()
    repository.get_public_destination.return_value = None
    with pytest.raises(DestinationNotFoundError):
        service.add_favorite(1, 7)
    session.rollback.assert_called_once()


def test_integrity_race_returns_existing_favorite() -> None:
    service, session, repository = make_service()
    favorite = make_favorite()
    repository.get_public_destination.return_value = favorite.destination
    repository.get_by_user_and_destination.side_effect = [None, favorite]
    repository.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    result = service.add_favorite(1, 7)
    assert result.id == favorite.id
    session.rollback.assert_called_once()
    assert repository.get_by_user_and_destination.call_count == 2
    repository.list_by_user.return_value = []
    repository.count_by_user.return_value = 0
    assert service.list_favorites(user_id=1, skip=0, limit=20).total == 0


def test_integrity_without_existing_row_raises_conflict() -> None:
    service, _, repository = make_service()
    repository.get_public_destination.return_value = make_destination()
    repository.get_by_user_and_destination.return_value = None
    repository.flush.side_effect = IntegrityError("insert", {}, Exception("constraint"))
    with pytest.raises(FavoriteIntegrityError):
        service.add_favorite(1, 7)


def test_duplicate_recovery_read_failure_is_generic_and_rolls_back() -> None:
    service, session, repository = make_service()
    repository.get_public_destination.return_value = make_destination()
    repository.get_by_user_and_destination.side_effect = [
        None,
        SQLAlchemyError("recovery read failed"),
    ]
    repository.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    session.is_active = False
    with pytest.raises(FavoritePersistenceError):
        service.add_favorite(1, 7)
    assert session.rollback.call_count == 2


def test_add_persistence_failure_rolls_back() -> None:
    service, session, repository = make_service()
    repository.get_public_destination.side_effect = SQLAlchemyError("down")
    with pytest.raises(FavoritePersistenceError):
        service.add_favorite(1, 7)
    session.rollback.assert_called_once()


def test_delete_is_idempotent() -> None:
    service, session, repository = make_service()
    repository.get_by_user_and_destination.return_value = None
    service.delete_favorite(1, 7)
    repository.delete.assert_not_called()
    session.commit.assert_not_called()

    repository.get_by_user_and_destination.return_value = make_favorite()
    service.delete_favorite(1, 7)
    repository.delete.assert_called_once()
    repository.flush.assert_called_once()
    session.commit.assert_called_once()


def test_private_or_inactive_destination_cannot_be_added_or_checked() -> None:
    service, _, repository = make_service()
    repository.get_public_destination.return_value = None
    with pytest.raises(DestinationNotFoundError):
        service.add_favorite(1, 7)
    with pytest.raises(DestinationNotFoundError):
        service.check_favorite(1, 7)


def test_validation_rejects_invalid_ids_and_pagination() -> None:
    service, _, _ = make_service()
    with pytest.raises(ValueError):
        service.add_favorite(1, 0)
    with pytest.raises(ValueError):
        service.list_favorites(user_id=1, skip=-1, limit=20)
    with pytest.raises(ValueError):
        service.list_favorites(user_id=1, skip=0, limit=101)


def test_list_and_check_favorites() -> None:
    service, _, repository = make_service()
    favorite = make_favorite()
    repository.list_by_user.return_value = [favorite]
    repository.count_by_user.return_value = 1
    response = service.list_favorites(user_id=1, skip=0, limit=20)
    assert response.total == 1
    assert response.items[0].destination.name_en == "Leptis Magna"

    repository.get_public_destination.return_value = favorite.destination
    repository.get_by_user_and_destination.return_value = favorite
    assert service.check_favorite(1, 7).is_favorite is True


def test_primary_media_is_selected_deterministically() -> None:
    destination = make_destination()
    now = datetime.now(UTC)
    older_media = MediaAsset(
        id=1,
        file_name="older.jpg",
        file_path="/older.jpg",
        public_url=None,
        mime_type="image/jpeg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    newer_media = MediaAsset(
        id=2,
        file_name="newer.jpg",
        file_path="/newer.jpg",
        public_url="/public/newer.jpg",
        mime_type="image/jpeg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    destination.media_items = [
        DestinationMedia(
            id=1,
            destination_id=destination.id,
            media_id=older_media.id,
            media=older_media,
            is_primary=True,
            sort_order=0,
            created_at=now,
            updated_at=now,
        ),
        DestinationMedia(
            id=2,
            destination_id=destination.id,
            media_id=newer_media.id,
            media=newer_media,
            is_primary=True,
            sort_order=0,
            created_at=now,
            updated_at=now,
        ),
    ]
    result = FavoriteService._to_read(make_favorite(destination))
    assert result.destination.primary_media_url == "/public/newer.jpg"


@pytest.mark.parametrize("operation", ["list", "delete", "check"])
def test_sqlalchemy_errors_map_to_persistence_error(operation: str) -> None:
    service, session, repository = make_service()
    if operation == "list":
        repository.list_by_user.side_effect = SQLAlchemyError("down")
        call = lambda: service.list_favorites(user_id=1, skip=0, limit=20)
    elif operation == "delete":
        repository.get_by_user_and_destination.side_effect = SQLAlchemyError("down")
        call = lambda: service.delete_favorite(1, 7)
    else:
        repository.get_public_destination.side_effect = SQLAlchemyError("down")
        call = lambda: service.check_favorite(1, 7)
    with pytest.raises(FavoritePersistenceError):
        call()
    if operation == "delete":
        session.rollback.assert_called_once()
