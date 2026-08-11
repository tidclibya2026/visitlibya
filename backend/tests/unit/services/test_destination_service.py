from unittest.mock import MagicMock

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    CategoryNotFoundError,
    DestinationIntegrityError,
    DestinationNotFoundError,
    DestinationPersistenceError,
    DestinationSlugConflictError,
    DestinationTranslationConflictError,
)
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.schemas.destination import (
    DestinationCreate,
    DestinationTranslationCreate,
    DestinationUpdate,
)
from app.services.destination import DestinationService


class FakeDestinationRepository:
    def __init__(self) -> None:
        self.destinations: dict[int, Destination] = {}
        self.slug_conflict = False
        self.valid_categories = {1}
        self.flush_error: Exception | None = None
        self.deleted: Destination | None = None

    def get_by_id(self, destination_id: int) -> Destination | None:
        return self.destinations.get(destination_id)

    def get_by_slug(self, slug: str) -> Destination | None:
        return next(
            (item for item in self.destinations.values() if item.slug == slug),
            None,
        )

    def get_public_by_slug(self, slug: str) -> Destination | None:
        destination = self.get_by_slug(slug)
        if destination is None:
            return None
        return destination if destination.status == DestinationStatus.PUBLISHED and destination.is_active else None

    def slug_exists(
        self,
        slug: str,
        exclude_destination_id: int | None = None,
    ) -> bool:
        if self.slug_conflict:
            return True
        return any(
            item.slug == slug and item.id != exclude_destination_id
            for item in self.destinations.values()
        )

    def category_exists(self, category_id: int) -> bool:
        return category_id in self.valid_categories

    def count(self, **filters: object) -> int:
        return len(self.destinations)

    def list(self, *, skip: int, limit: int, **filters: object) -> list[Destination]:
        return list(self.destinations.values())[skip : skip + limit]

    def add(self, destination: Destination) -> None:
        destination.id = max(self.destinations, default=0) + 1
        self.destinations[destination.id] = destination

    def delete(self, destination: Destination) -> None:
        self.deleted = destination
        self.destinations.pop(destination.id, None)

    def flush(self) -> None:
        if self.flush_error is not None:
            raise self.flush_error

    def refresh(self, destination: Destination) -> None:
        destination.category = None


def make_create_payload(
    *,
    slug: str = "leptis-magna",
    category_id: int | None = 1,
    language_code: str = "ar",
) -> DestinationCreate:
    return DestinationCreate(
        slug=slug,
        category_id=category_id,
        latitude=32.6389,
        longitude=14.2906,
        translations=[
            DestinationTranslationCreate(
                language_code=language_code,
                name="لبدة الكبرى",
            )
        ],
    )


def make_service() -> tuple[DestinationService, MagicMock, FakeDestinationRepository]:
    session = MagicMock()
    session.is_active = True
    repository = FakeDestinationRepository()
    service = DestinationService(session, repository)  # type: ignore[arg-type]
    return service, session, repository


def test_create_commits_and_builds_geometry_with_srid_4326() -> None:
    service, session, repository = make_service()

    destination = service.create_destination(make_create_payload(language_code=" AR "))

    assert destination.id == 1
    assert destination.translations[0].language_code == "ar"
    assert isinstance(destination.geometry, WKTElement)
    assert destination.geometry.srid == 4326
    assert str(destination.geometry) == "POINT(14.2906 32.6389)"
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    assert repository.get_by_id(1) is destination


def test_public_list_is_always_published_and_active() -> None:
    service, _, repository = make_service()
    captured: dict[str, object] = {}
    repository.count = lambda **filters: captured.update(filters) or 0  # type: ignore[method-assign]
    repository.list = lambda **arguments: []  # type: ignore[method-assign]

    items, total = service.list_public_destinations(
        skip=0, limit=20, category_id=None, region=None,
        municipality=None, is_featured=None,
    )

    assert items == [] and total == 0
    assert captured["status"] == DestinationStatus.PUBLISHED
    assert captured["is_active"] is True


@pytest.mark.parametrize(
    ("status", "is_active", "visible"),
    [
        (DestinationStatus.PUBLISHED, True, True),
        (DestinationStatus.DRAFT, True, False),
        (DestinationStatus.UNDER_REVIEW, True, False),
        (DestinationStatus.APPROVED, True, False),
        (DestinationStatus.ARCHIVED, True, False),
        (DestinationStatus.PUBLISHED, False, False),
    ],
)
def test_public_detail_hides_non_public_states(status, is_active, visible) -> None:
    service, _, repository = make_service()
    destination = Destination(
        id=1, slug="leptis-magna", status=status, is_active=is_active,
        latitude=32.6389, longitude=14.2906,
    )
    destination.translations = []
    repository.destinations[1] = destination

    if visible:
        assert service.get_public_destination_by_slug("leptis-magna") is destination
    else:
        with pytest.raises(DestinationNotFoundError):
            service.get_public_destination_by_slug("leptis-magna")


def test_create_rejects_missing_category() -> None:
    service, session, _ = make_service()

    with pytest.raises(CategoryNotFoundError):
        service.create_destination(make_create_payload(category_id=99))

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_create_rejects_slug_conflict() -> None:
    service, session, repository = make_service()
    repository.slug_conflict = True

    with pytest.raises(DestinationSlugConflictError):
        service.create_destination(make_create_payload())

    session.rollback.assert_called_once_with()


def test_duplicate_language_detection_is_case_insensitive() -> None:
    translations = [
        DestinationTranslationCreate(language_code="ar", name="الأولى"),
        DestinationTranslationCreate(language_code="en", name="Second"),
    ]
    translations[1].language_code = " AR "

    with pytest.raises(DestinationTranslationConflictError):
        DestinationService._ensure_unique_translation_languages(translations)


def test_update_synchronizes_translations_without_case_duplicates() -> None:
    service, session, repository = make_service()
    destination = Destination(id=1, slug="leptis-magna", category_id=1)
    existing = DestinationTranslation(
        id=1,
        destination_id=1,
        language_code="AR",
        name="الاسم القديم",
    )
    destination.translations = [existing]
    repository.destinations[1] = destination
    payload = DestinationUpdate(
        slug="leptis-magna-updated",
        translations=[
            DestinationTranslationCreate(language_code="ar", name="الاسم الجديد"),
            DestinationTranslationCreate(language_code="en", name="New name"),
        ],
    )

    updated = service.update_destination(1, payload)

    assert updated.slug == "leptis-magna-updated"
    assert len(updated.translations) == 2
    assert updated.translations[0] is existing
    assert existing.language_code == "ar"
    assert existing.name == "الاسم الجديد"
    assert {item.language_code for item in updated.translations} == {"ar", "en"}
    session.commit.assert_called_once_with()


def test_delete_uses_hard_delete_and_commits() -> None:
    service, session, repository = make_service()
    destination = Destination(id=1, slug="leptis-magna")
    destination.translations = []
    repository.destinations[1] = destination

    service.delete_destination(1)

    assert repository.deleted is destination
    assert repository.destinations == {}
    session.commit.assert_called_once_with()


def test_integrity_error_rolls_back() -> None:
    service, session, repository = make_service()
    repository.flush_error = IntegrityError("insert", {}, Exception("duplicate"))

    with pytest.raises(DestinationIntegrityError):
        service.create_destination(make_create_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_sqlalchemy_error_rolls_back() -> None:
    service, session, repository = make_service()
    repository.flush_error = SQLAlchemyError("database unavailable")

    with pytest.raises(DestinationPersistenceError):
        service.create_destination(make_create_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
