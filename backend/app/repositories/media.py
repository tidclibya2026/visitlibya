from collections.abc import Sequence

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.destination import Destination
from app.models.media import DestinationMedia, MediaAsset
from app.repositories.base import BaseRepository
from app.repositories.sorting import safe_order_by
from app.schemas.media import MediaSortField, MediaSortOrder


class MediaRepository(BaseRepository[MediaAsset]):
    @staticmethod
    def _build_filters(
        *,
        mime_type: str | None,
        is_active: bool | None,
        destination_id: int | None,
        is_primary: bool | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if mime_type is not None:
            filters.append(MediaAsset.mime_type == mime_type)
        if is_active is not None:
            filters.append(MediaAsset.is_active == is_active)
        if destination_id is not None:
            filters.append(DestinationMedia.destination_id == destination_id)
        if is_primary is not None:
            filters.append(DestinationMedia.is_primary == is_primary)
        return filters

    @staticmethod
    def _needs_link_join(
        destination_id: int | None,
        is_primary: bool | None,
    ) -> bool:
        return destination_id is not None or is_primary is not None

    def get_by_id(self, media_id: int) -> MediaAsset | None:
        return self.session.scalar(
            select(MediaAsset)
            .options(selectinload(MediaAsset.destination_links))
            .where(MediaAsset.id == media_id)
        )

    def path_exists(self, file_path: str, exclude_media_id: int | None = None) -> bool:
        statement = select(MediaAsset.id).where(MediaAsset.file_path == file_path)
        if exclude_media_id is not None:
            statement = statement.where(MediaAsset.id != exclude_media_id)
        return self.session.scalar(statement.limit(1)) is not None

    def list(
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
    ) -> Sequence[MediaAsset]:
        filters = self._build_filters(
            mime_type=mime_type,
            is_active=is_active,
            destination_id=destination_id,
            is_primary=is_primary,
        )
        statement = select(MediaAsset).options(
            selectinload(MediaAsset.destination_links)
        )
        if self._needs_link_join(destination_id, is_primary):
            statement = statement.join(DestinationMedia)
        ordering = safe_order_by(
            sort_by,
            sort_order,
            {
                "id": MediaAsset.id,
                "file_name": MediaAsset.file_name,
                "mime_type": MediaAsset.mime_type,
                "file_size": MediaAsset.file_size,
                "created_at": MediaAsset.created_at,
            },
        )
        statement = statement.where(*filters).order_by(ordering).offset(skip).limit(limit)
        return self.session.scalars(statement).unique().all()

    def count(
        self,
        *,
        mime_type: str | None,
        is_active: bool | None,
        destination_id: int | None,
        is_primary: bool | None,
    ) -> int:
        filters = self._build_filters(
            mime_type=mime_type,
            is_active=is_active,
            destination_id=destination_id,
            is_primary=is_primary,
        )
        statement: Select[tuple[int]] = select(func.count(func.distinct(MediaAsset.id)))
        if self._needs_link_join(destination_id, is_primary):
            statement = statement.join(DestinationMedia)
        return self.session.scalar(statement.where(*filters)) or 0

    def destination_exists(self, destination_id: int) -> bool:
        return self.session.scalar(
            select(Destination.id).where(Destination.id == destination_id).limit(1)
        ) is not None

    def get_link(self, destination_id: int, media_id: int) -> DestinationMedia | None:
        return self.session.scalar(
            select(DestinationMedia).where(
                DestinationMedia.destination_id == destination_id,
                DestinationMedia.media_id == media_id,
            )
        )

    def add_link(self, link: DestinationMedia) -> None:
        self.session.add(link)

    def delete_link(self, link: DestinationMedia) -> None:
        self.session.delete(link)

    def clear_primary(self, destination_id: int, exclude_media_id: int) -> None:
        self.session.execute(
            update(DestinationMedia)
            .where(
                DestinationMedia.destination_id == destination_id,
                DestinationMedia.media_id != exclude_media_id,
                DestinationMedia.is_primary.is_(True),
            )
            .values(is_primary=False)
        )

    def refresh(self, media: MediaAsset) -> None:
        self.session.refresh(media, attribute_names=["destination_links"])

    def refresh_link(self, link: DestinationMedia) -> None:
        self.session.refresh(link)
