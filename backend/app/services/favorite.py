from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DestinationNotFoundError,
    FavoriteIntegrityError,
    FavoritePersistenceError,
)
from app.models.destination import DestinationTranslation
from app.models.favorite import Favorite
from app.models.media import DestinationMedia
from app.repositories.favorite import FavoriteRepository
from app.schemas.favorite import (
    FavoriteCategoryItem,
    FavoriteCheckResponse,
    FavoriteDestinationItem,
    FavoriteListResponse,
    FavoriteRead,
)


class FavoriteService:
    def __init__(
        self,
        session: Session,
        repository: FavoriteRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or FavoriteRepository(session)

    def add_favorite(self, user_id: int, destination_id: int) -> FavoriteRead:
        self._validate_ids(user_id, destination_id)
        try:
            destination = self.repository.get_public_destination(destination_id)
            if destination is None:
                raise DestinationNotFoundError()
            existing = self.repository.get_by_user_and_destination(
                user_id,
                destination_id,
            )
            if existing is not None:
                return self._to_read(existing)

            favorite = Favorite(
                user_id=user_id,
                destination_id=destination_id,
                destination=destination,
            )
            self.repository.add(favorite)
            self.repository.flush()
            self.session.commit()
            return self._to_read(favorite)
        except DestinationNotFoundError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            try:
                existing = self.repository.get_by_user_and_destination(
                    user_id,
                    destination_id,
                )
            except SQLAlchemyError as read_exc:
                self._rollback_failed_read()
                raise FavoritePersistenceError() from read_exc
            if existing is not None:
                return self._to_read(existing)
            raise FavoriteIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise FavoritePersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def delete_favorite(self, user_id: int, destination_id: int) -> None:
        self._validate_ids(user_id, destination_id)
        try:
            favorite = self.repository.get_by_user_and_destination(
                user_id,
                destination_id,
            )
            if favorite is None:
                return
            self.repository.delete(favorite)
            self.repository.flush()
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise FavoritePersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def list_favorites(
        self,
        *,
        user_id: int,
        skip: int,
        limit: int,
    ) -> FavoriteListResponse:
        self._validate_list_parameters(user_id, skip, limit)
        try:
            items = self.repository.list_by_user(
                user_id=user_id,
                skip=skip,
                limit=limit,
            )
            total = self.repository.count_by_user(user_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise FavoritePersistenceError() from exc
        return FavoriteListResponse(
            items=[self._to_read(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    def check_favorite(
        self,
        user_id: int,
        destination_id: int,
    ) -> FavoriteCheckResponse:
        self._validate_ids(user_id, destination_id)
        try:
            if self.repository.get_public_destination(destination_id) is None:
                raise DestinationNotFoundError()
            favorite = self.repository.get_by_user_and_destination(
                user_id,
                destination_id,
            )
        except DestinationNotFoundError:
            raise
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise FavoritePersistenceError() from exc
        return FavoriteCheckResponse(
            destination_id=destination_id,
            is_favorite=favorite is not None,
        )

    @staticmethod
    def _validate_ids(user_id: int, destination_id: int) -> None:
        if user_id < 1 or destination_id < 1:
            raise ValueError("user_id and destination_id must be positive")

    @staticmethod
    def _validate_list_parameters(user_id: int, skip: int, limit: int) -> None:
        if user_id < 1 or skip < 0 or not 1 <= limit <= 100:
            raise ValueError("Invalid favorite list parameters")

    @classmethod
    def _to_read(cls, favorite: Favorite) -> FavoriteRead:
        destination = favorite.destination
        translations = {
            translation.language_code.lower(): translation
            for translation in destination.translations
        }
        category = destination.category
        primary_media_url = cls._primary_media_url(destination.media_items)
        return FavoriteRead(
            id=favorite.id,
            destination=FavoriteDestinationItem(
                id=destination.id,
                slug=destination.slug,
                name_ar=cls._translation_value(translations.get("ar")),
                name_en=cls._translation_value(translations.get("en")),
                municipality=destination.municipality,
                region=destination.region,
                category=(
                    FavoriteCategoryItem(
                        id=category.id,
                        code=category.code,
                        name_ar=category.name_ar,
                        name_en=category.name_en,
                    )
                    if category is not None
                    else None
                ),
                primary_media_url=primary_media_url,
                is_featured=destination.is_featured,
            ),
            created_at=favorite.created_at,
        )

    @staticmethod
    def _translation_value(
        translation: DestinationTranslation | None,
    ) -> str | None:
        return translation.name if translation is not None else None

    @staticmethod
    def _primary_media_url(
        media_items: Sequence[DestinationMedia],
    ) -> str | None:
        candidates = [
            item
            for item in media_items
            if item.is_primary and item.media.is_active
        ]
        if not candidates:
            return None
        selected = max(candidates, key=lambda item: (item.created_at, item.id))
        return selected.media.public_url or selected.media.file_path

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
