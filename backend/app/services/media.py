from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DestinationMediaConflictError,
    DestinationMediaNotFoundError,
    DestinationNotFoundError,
    MediaAssetIntegrityError,
    MediaAssetNotFoundError,
    MediaAssetPathConflictError,
    MediaAssetPersistenceError,
    MediaError,
)
from app.models.media import DestinationMedia, MediaAsset
from app.repositories.media import MediaRepository
from app.schemas.media import (
    DestinationMediaCreate,
    DestinationMediaUpdate,
    MediaAssetCreate,
    MediaAssetUpdate,
    MediaSortField,
    MediaSortOrder,
)


class MediaService:
    def __init__(self, session: Session, repository: MediaRepository | None = None) -> None:
        self.session = session
        self.repository = repository or MediaRepository(session)

    def list_media(
        self,
        *,
        skip: int,
        limit: int,
        mime_type: str | None,
        is_active: bool | None,
        destination_id: int | None,
        is_primary: bool | None,
        sort_by: MediaSortField,
        sort_order: MediaSortOrder,
    ) -> tuple[Sequence[MediaAsset], int]:
        try:
            filters = {
                "mime_type": mime_type,
                "is_active": is_active,
                "destination_id": destination_id,
                "is_primary": is_primary,
            }
            total = self.repository.count(**filters)
            items = self.repository.list(
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order,
                **filters,
            )
            return items, total
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise MediaAssetPersistenceError() from exc

    def get_media(self, media_id: int) -> MediaAsset:
        try:
            media = self.repository.get_by_id(media_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise MediaAssetPersistenceError() from exc
        if media is None:
            raise MediaAssetNotFoundError()
        return media

    def create_media(self, payload: MediaAssetCreate) -> MediaAsset:
        try:
            self._ensure_path_available(payload.file_path)
            media = MediaAsset(**payload.model_dump())
            self.repository.add(media)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(media)
            return media
        except MediaError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_media(self, media_id: int, payload: MediaAssetUpdate) -> MediaAsset:
        try:
            media = self._get_required_media(media_id)
            values = payload.model_dump(exclude_unset=True)
            file_path = values.get("file_path")
            if file_path is not None:
                self._ensure_path_available(file_path, exclude_media_id=media_id)
            for field, value in values.items():
                setattr(media, field, value)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(media)
            return media
        except MediaError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def delete_media(self, media_id: int) -> None:
        try:
            media = self._get_required_media(media_id)
            self.repository.delete(media)
            self.repository.flush()
            self.session.commit()
        except MediaError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def associate_destination(
        self,
        media_id: int,
        destination_id: int,
        payload: DestinationMediaCreate,
    ) -> DestinationMedia:
        try:
            self._get_required_media(media_id)
            self._ensure_destination_exists(destination_id)
            if self.repository.get_link(destination_id, media_id) is not None:
                raise DestinationMediaConflictError()
            if payload.is_primary:
                self.repository.clear_primary(destination_id, media_id)
            link = DestinationMedia(
                destination_id=destination_id,
                media_id=media_id,
                **payload.model_dump(),
            )
            self.repository.add_link(link)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh_link(link)
            return link
        except (MediaError, DestinationNotFoundError):
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_destination_link(
        self,
        media_id: int,
        destination_id: int,
        payload: DestinationMediaUpdate,
    ) -> DestinationMedia:
        try:
            link = self._get_required_link(destination_id, media_id)
            values = payload.model_dump(exclude_unset=True)
            if values.get("is_primary") is True:
                self.repository.clear_primary(destination_id, media_id)
            for field, value in values.items():
                setattr(link, field, value)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh_link(link)
            return link
        except MediaError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def remove_destination(self, media_id: int, destination_id: int) -> None:
        try:
            link = self._get_required_link(destination_id, media_id)
            self.repository.delete_link(link)
            self.repository.flush()
            self.session.commit()
        except MediaError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise MediaAssetIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise MediaAssetPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def _ensure_path_available(self, file_path: str, exclude_media_id: int | None = None) -> None:
        if self.repository.path_exists(file_path, exclude_media_id):
            raise MediaAssetPathConflictError()

    def _ensure_destination_exists(self, destination_id: int) -> None:
        if not self.repository.destination_exists(destination_id):
            raise DestinationNotFoundError()

    def _get_required_media(self, media_id: int) -> MediaAsset:
        media = self.repository.get_by_id(media_id)
        if media is None:
            raise MediaAssetNotFoundError()
        return media

    def _get_required_link(self, destination_id: int, media_id: int) -> DestinationMedia:
        link = self.repository.get_link(destination_id, media_id)
        if link is None:
            raise DestinationMediaNotFoundError()
        return link

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
