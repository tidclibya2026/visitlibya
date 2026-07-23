from unittest.mock import MagicMock

from app.models.media import DestinationMedia, MediaAsset
from app.repositories.media import MediaRepository


def test_get_path_exists_and_destination_exists() -> None:
    media = MediaAsset(id=1, file_name="a.jpg", file_path="/a.jpg", mime_type="image/jpeg")
    session = MagicMock()
    session.scalar.side_effect = [media, 1, None, 7]
    repository = MediaRepository(session)

    assert repository.get_by_id(1) is media
    assert repository.path_exists("/a.jpg") is True
    assert repository.path_exists("/a.jpg", exclude_media_id=1) is False
    assert repository.destination_exists(7) is True


def test_list_and_count_apply_filters_and_ordering() -> None:
    media = MediaAsset(id=1, file_name="a.jpg", file_path="/a.jpg", mime_type="image/jpeg")
    result = MagicMock()
    result.unique.return_value.all.return_value = [media]
    session = MagicMock()
    session.scalars.return_value = result
    session.scalar.return_value = 1
    repository = MediaRepository(session)

    items = repository.list(skip=0, limit=20, mime_type="image/jpeg", is_active=True, destination_id=7, is_primary=True, sort_by="created_at", sort_order="desc")
    total = repository.count(mime_type="image/jpeg", is_active=True, destination_id=7, is_primary=True)

    assert list(items) == [media]
    assert total == 1
    statement = str(session.scalars.call_args.args[0])
    assert "destination_media" in statement
    assert "mime_type" in statement
    assert "DESC" in statement


def test_link_operations_and_primary_update() -> None:
    link = DestinationMedia(destination_id=7, media_id=1)
    session = MagicMock()
    session.scalar.return_value = link
    repository = MediaRepository(session)

    assert repository.get_link(7, 1) is link
    repository.add_link(link)
    repository.clear_primary(7, 1)
    repository.refresh_link(link)
    repository.delete_link(link)

    session.add.assert_called_once_with(link)
    session.execute.assert_called_once()
    assert "is_primary" in str(session.execute.call_args.args[0])
    session.refresh.assert_called_once_with(link)
    session.delete.assert_called_once_with(link)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_common_write_helpers_do_not_manage_transactions() -> None:
    media = MediaAsset(file_name="a.jpg", file_path="/a.jpg", mime_type="image/jpeg")
    session = MagicMock()
    repository = MediaRepository(session)

    repository.add(media)
    repository.flush()
    repository.refresh(media)
    repository.delete(media)

    session.add.assert_called_once_with(media)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(media, attribute_names=["destination_links"])
    session.delete.assert_called_once_with(media)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
