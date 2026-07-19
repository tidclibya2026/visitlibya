from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    DestinationMediaConflictError,
    DestinationMediaNotFoundError,
    DestinationNotFoundError,
    MediaAssetIntegrityError,
    MediaAssetNotFoundError,
    MediaAssetPathConflictError,
    MediaAssetPersistenceError,
)
from app.models.media import DestinationMedia, MediaAsset
from app.schemas.media import DestinationMediaCreate, DestinationMediaUpdate, MediaAssetCreate, MediaAssetUpdate
from app.services.media import MediaService


class FakeMediaRepository:
    def __init__(self) -> None:
        self.media: dict[int, MediaAsset] = {}
        self.links: dict[tuple[int, int], DestinationMedia] = {}
        self.destinations = {7}
        self.path_conflict = False
        self.flush_error: Exception | None = None
        self.read_error: Exception | None = None
        self.cleared: tuple[int, int] | None = None

    def get_by_id(self, media_id: int) -> MediaAsset | None:
        if self.read_error:
            raise self.read_error
        return self.media.get(media_id)

    def path_exists(self, file_path: str, exclude_media_id: int | None = None) -> bool:
        return self.path_conflict or any(item.file_path == file_path and item.id != exclude_media_id for item in self.media.values())

    def list(self, **_: object) -> list[MediaAsset]:
        if self.read_error:
            raise self.read_error
        return list(self.media.values())

    def count(self, **_: object) -> int:
        if self.read_error:
            raise self.read_error
        return len(self.media)

    def add(self, media: MediaAsset) -> None:
        media.id = max(self.media, default=0) + 1
        media.destination_links = []
        self.media[media.id] = media

    def delete(self, media: MediaAsset) -> None:
        self.media.pop(media.id, None)

    def flush(self) -> None:
        if self.flush_error:
            raise self.flush_error

    def refresh(self, media: MediaAsset) -> None: pass
    def destination_exists(self, destination_id: int) -> bool: return destination_id in self.destinations
    def get_link(self, destination_id: int, media_id: int) -> DestinationMedia | None: return self.links.get((destination_id, media_id))
    def add_link(self, link: DestinationMedia) -> None:
        link.id = 1
        self.links[(link.destination_id, link.media_id)] = link
    def delete_link(self, link: DestinationMedia) -> None: self.links.pop((link.destination_id, link.media_id), None)
    def clear_primary(self, destination_id: int, exclude_media_id: int) -> None:
        self.cleared = (destination_id, exclude_media_id)
        for (destination, media_id), link in self.links.items():
            if destination == destination_id and media_id != exclude_media_id: link.is_primary = False
    def refresh_link(self, link: DestinationMedia) -> None: pass


def make_service() -> tuple[MediaService, MagicMock, FakeMediaRepository]:
    session = MagicMock(); session.is_active = True
    repository = FakeMediaRepository()
    return MediaService(session, repository), session, repository  # type: ignore[arg-type]


def payload(path: str = "/media/a.jpg") -> MediaAssetCreate:
    return MediaAssetCreate(file_name="a.jpg", file_path=path, mime_type="image/jpeg", copyright_owner="Visit Libya")


def test_create_update_delete_and_transactions() -> None:
    service, session, repository = make_service()
    media = service.create_media(payload())
    assert media.id == 1
    updated = service.update_media(1, MediaAssetUpdate(caption_en="Leptis Magna"))
    assert updated.caption_en == "Leptis Magna"
    service.delete_media(1)
    assert repository.media == {}
    assert session.commit.call_count == 3


def test_path_conflict_and_not_found() -> None:
    service, session, repository = make_service(); repository.path_conflict = True
    with pytest.raises(MediaAssetPathConflictError): service.create_media(payload())
    with pytest.raises(MediaAssetNotFoundError): service.get_media(404)
    session.rollback.assert_called_once_with()


def test_list_and_read_sqlalchemy_error() -> None:
    service, session, repository = make_service(); repository.read_error = SQLAlchemyError("down")
    with pytest.raises(MediaAssetPersistenceError): service.list_media(skip=0, limit=20, mime_type=None, is_active=True, destination_id=None, is_primary=None, sort_by="id", sort_order="asc")
    session.rollback.assert_not_called()


def test_associate_primary_clears_previous_and_commits() -> None:
    service, session, repository = make_service()
    media = MediaAsset(id=1, file_name="a.jpg", file_path="/a.jpg", mime_type="image/jpeg"); repository.media[1] = media
    old = DestinationMedia(id=2, destination_id=7, media_id=2, is_primary=True); repository.links[(7, 2)] = old
    link = service.associate_destination(1, 7, DestinationMediaCreate(sort_order=3, is_primary=True))
    assert link.is_primary is True and old.is_primary is False
    assert repository.cleared == (7, 1)
    session.commit.assert_called_once_with()


def test_association_conflict_missing_destination_and_removal() -> None:
    service, _, repository = make_service(); repository.media[1] = MediaAsset(id=1, file_name="a", file_path="/a", mime_type="image/jpeg")
    with pytest.raises(DestinationNotFoundError): service.associate_destination(1, 99, DestinationMediaCreate())
    repository.links[(7, 1)] = DestinationMedia(destination_id=7, media_id=1)
    with pytest.raises(DestinationMediaConflictError): service.associate_destination(1, 7, DestinationMediaCreate())
    service.remove_destination(1, 7)
    with pytest.raises(DestinationMediaNotFoundError): service.remove_destination(1, 7)


def test_update_link_assigns_primary() -> None:
    service, session, repository = make_service(); link = DestinationMedia(destination_id=7, media_id=1, is_primary=False); repository.links[(7, 1)] = link
    result = service.update_destination_link(1, 7, DestinationMediaUpdate(is_primary=True, sort_order=4))
    assert result.is_primary is True and result.sort_order == 4
    assert repository.cleared == (7, 1)
    session.commit.assert_called_once_with()


@pytest.mark.parametrize("error, expected", [(IntegrityError("x", {}, Exception()), MediaAssetIntegrityError), (SQLAlchemyError("x"), MediaAssetPersistenceError)])
def test_write_errors_rollback(error: Exception, expected: type[Exception]) -> None:
    service, session, repository = make_service(); repository.flush_error = error
    with pytest.raises(expected): service.create_media(payload())
    session.rollback.assert_called_once_with(); session.commit.assert_not_called()
