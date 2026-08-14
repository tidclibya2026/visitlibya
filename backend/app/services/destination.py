from collections.abc import Sequence

from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CategoryNotFoundError,
    DestinationCoordinatesError,
    DestinationError,
    DestinationIntegrityError,
    DestinationNotFoundError,
    DestinationPersistenceError,
    DestinationPublicationBlockedError,
    DestinationSlugConflictError,
    DestinationTranslationConflictError,
)
from app.models.destination import (
    Destination,
    DestinationStatus,
    DestinationTranslation,
)
from app.repositories.destination import DestinationRepository
from app.schemas.destination import (
    DestinationCreate,
    DestinationTranslationCreate,
    DestinationUpdate,
)
from app.publication.governance import LegacyDestinationCatalog
from pathlib import Path

LEGACY_CATALOG = LegacyDestinationCatalog(Path(__file__).resolve().parents[2] / "data/dev/destinations.json")


class DestinationService:
    def __init__(
        self,
        session: Session,
        repository: DestinationRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or DestinationRepository(session)

    def list_destinations(
        self,
        *,
        skip: int,
        limit: int,
        status: DestinationStatus | None,
        category_id: int | None,
        region: str | None,
        municipality: str | None,
        is_featured: bool | None,
        is_active: bool | None,
    ) -> tuple[Sequence[Destination], int]:
        try:
            total = self.repository.count(
                status=status,
                category_id=category_id,
                region=region,
                municipality=municipality,
                is_featured=is_featured,
                is_active=is_active,
            )
            items = self.repository.list(
                skip=skip,
                limit=limit,
                status=status,
                category_id=category_id,
                region=region,
                municipality=municipality,
                is_featured=is_featured,
                is_active=is_active,
            )
            return items, total
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise DestinationPersistenceError() from exc

    def list_public_destinations(
        self,
        *,
        skip: int,
        limit: int,
        category_id: int | None,
        region: str | None,
        municipality: str | None,
        is_featured: bool | None,
    ) -> tuple[Sequence[Destination], int]:
        items, _ = self.list_destinations(
            skip=skip,
            limit=limit,
            status=DestinationStatus.PUBLISHED,
            category_id=category_id,
            region=region,
            municipality=municipality,
            is_featured=is_featured,
            is_active=True,
        )
        eligible = [item for item in items if self._is_legacy_compatible(item)]
        return eligible, len(eligible)

    def get_public_destination_by_slug(self, slug: str) -> Destination:
        try:
            destination = self.repository.get_public_by_slug(slug)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise DestinationPersistenceError() from exc
        if destination is None or not self._is_legacy_compatible(destination):
            raise DestinationNotFoundError()
        return destination

    def get_destination_by_slug(self, slug: str) -> Destination:
        try:
            destination = self.repository.get_by_slug(slug)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise DestinationPersistenceError() from exc
        if destination is None:
            raise DestinationNotFoundError()
        return destination

    def get_destination_by_id(self, destination_id: int) -> Destination:
        try:
            destination = self.repository.get_by_id(destination_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise DestinationPersistenceError() from exc
        if destination is None:
            raise DestinationNotFoundError()
        return destination

    def create_destination(self, payload: DestinationCreate) -> Destination:
        try:
            self._ensure_slug_available(payload.slug)
            self._ensure_category_exists(payload.category_id)
            self._ensure_unique_translation_languages(payload.translations)

            values = payload.model_dump(exclude={"translations"})
            destination = Destination(**values)
            destination.translations = [
                DestinationTranslation(**self._translation_values(item))
                for item in payload.translations
            ]
            self._apply_coordinates(destination)

            self._prevent_publication_bypass(destination)

            self.repository.add(destination)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(destination)
            return destination
        except DestinationError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise DestinationIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DestinationPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_destination(
        self,
        destination_id: int,
        payload: DestinationUpdate,
    ) -> Destination:
        try:
            destination = self._get_required_destination(destination_id)
            values = payload.model_dump(exclude_unset=True, exclude={"translations"})

            new_slug = values.get("slug")
            if new_slug is not None:
                self._ensure_slug_available(
                    new_slug,
                    exclude_destination_id=destination_id,
                )

            if "category_id" in values:
                self._ensure_category_exists(values["category_id"])

            for field, value in values.items():
                setattr(destination, field, value)

            if payload.translations is not None:
                self._ensure_unique_translation_languages(payload.translations)
                self._synchronize_translations(destination, payload.translations)

            if "latitude" in values or "longitude" in values:
                if (destination.latitude is None) != (destination.longitude is None):
                    raise DestinationCoordinatesError()
                self._apply_coordinates(destination)

            self._prevent_publication_bypass(destination)

            self.repository.flush()
            self.session.commit()
            self.repository.refresh(destination)
            return destination
        except DestinationError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise DestinationIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DestinationPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def delete_destination(self, destination_id: int) -> None:
        try:
            destination = self._get_required_destination(destination_id)
            self.repository.delete(destination)
            self.repository.flush()
            self.session.commit()
        except DestinationError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise DestinationIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DestinationPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def _ensure_slug_available(
        self,
        slug: str,
        exclude_destination_id: int | None = None,
    ) -> None:
        if self.repository.slug_exists(slug, exclude_destination_id):
            raise DestinationSlugConflictError()

    def _get_required_destination(self, destination_id: int) -> Destination:
        destination = self.repository.get_by_id(destination_id)
        if destination is None:
            raise DestinationNotFoundError()
        return destination

    def _ensure_category_exists(self, category_id: int | None) -> None:
        if category_id is not None and not self.repository.category_exists(category_id):
            raise CategoryNotFoundError()

    @staticmethod
    def _ensure_unique_translation_languages(
        translations: Sequence[DestinationTranslationCreate],
    ) -> None:
        language_codes = [item.language_code.strip().lower() for item in translations]
        if len(language_codes) != len(set(language_codes)):
            raise DestinationTranslationConflictError()

    @staticmethod
    def _translation_values(
        translation: DestinationTranslationCreate,
    ) -> dict[str, object]:
        values = translation.model_dump()
        values["language_code"] = translation.language_code.strip().lower()
        return values

    @staticmethod
    def _apply_coordinates(destination: Destination) -> None:
        if destination.latitude is None or destination.longitude is None:
            destination.geometry = None
            return
        destination.geometry = WKTElement(
            f"POINT({destination.longitude} {destination.latitude})",
            srid=4326,
        )

    @staticmethod
    def _synchronize_translations(
        destination: Destination,
        translations: Sequence[DestinationTranslationCreate],
    ) -> None:
        incoming = {
            item.language_code.strip().lower(): item
            for item in translations
        }
        for existing in list(destination.translations):
            normalized_language_code = existing.language_code.strip().lower()
            payload = incoming.pop(normalized_language_code, None)
            if payload is None:
                destination.translations.remove(existing)
                continue
            for field, value in DestinationService._translation_values(payload).items():
                setattr(existing, field, value)
        destination.translations.extend(
            DestinationTranslation(**DestinationService._translation_values(item))
            for item in incoming.values()
        )

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()

    @staticmethod
    def _snapshot(destination: Destination) -> dict[str, object]:
        category = destination.category.code if destination.category is not None else None
        return {
            "slug": destination.slug, "category": category,
            "status": destination.status.value if isinstance(destination.status, DestinationStatus) else destination.status,
            "is_active": destination.is_active, "is_featured": destination.is_featured,
            "priority_order": destination.priority_order, "municipality": destination.municipality,
            "region": destination.region, "latitude": destination.latitude, "longitude": destination.longitude,
            "translations": [
                {name: getattr(item, name) for name in (
                    "language_code", "name", "short_description", "description",
                    "historical_background", "visitor_information",
                    "accessibility_information", "seo_title", "seo_description")}
                for item in destination.translations
            ],
        }

    @classmethod
    def _is_legacy_compatible(cls, destination: Destination) -> bool:
        return LEGACY_CATALOG.matches(cls._snapshot(destination))

    @classmethod
    def _prevent_publication_bypass(cls, destination: Destination) -> None:
        if destination.status in {DestinationStatus.PUBLISHED, DestinationStatus.APPROVED}:
            if destination.status is DestinationStatus.APPROVED or not cls._is_legacy_compatible(destination):
                raise DestinationPublicationBlockedError()
