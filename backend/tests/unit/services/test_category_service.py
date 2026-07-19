from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    CategoryCodeConflictError,
    CategoryIntegrityError,
    CategoryNotFoundError,
    CategoryPersistenceError,
)
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category import CategoryService


class FakeCategoryRepository:
    def __init__(self) -> None:
        self.categories: dict[int, Category] = {}
        self.code_conflict = False
        self.flush_error: Exception | None = None
        self.read_error: Exception | None = None
        self.deleted: Category | None = None

    def get_by_id(self, category_id: int) -> Category | None:
        if self.read_error is not None:
            raise self.read_error
        return self.categories.get(category_id)

    def get_by_code(self, code: str) -> Category | None:
        if self.read_error is not None:
            raise self.read_error
        return next(
            (category for category in self.categories.values() if category.code == code),
            None,
        )

    def code_exists(
        self,
        code: str,
        exclude_category_id: int | None = None,
    ) -> bool:
        if self.code_conflict:
            return True
        return any(
            category.code == code and category.id != exclude_category_id
            for category in self.categories.values()
        )

    def list(self, *, skip: int, limit: int, is_active: bool | None) -> list[Category]:
        categories = list(self.categories.values())
        if is_active is not None:
            categories = [item for item in categories if item.is_active == is_active]
        return categories[skip : skip + limit]

    def count(self, *, is_active: bool | None) -> int:
        return len(self.list(skip=0, limit=1000, is_active=is_active))

    def add(self, category: Category) -> None:
        category.id = max(self.categories, default=0) + 1
        self.categories[category.id] = category

    def delete(self, category: Category) -> None:
        self.deleted = category
        self.categories.pop(category.id, None)

    def flush(self) -> None:
        if self.flush_error is not None:
            raise self.flush_error

    def refresh(self, category: Category) -> None:
        return None


def make_service() -> tuple[CategoryService, MagicMock, FakeCategoryRepository]:
    session = MagicMock()
    session.is_active = True
    repository = FakeCategoryRepository()
    service = CategoryService(session, repository)  # type: ignore[arg-type]
    return service, session, repository


def make_payload(code: str = "heritage") -> CategoryCreate:
    return CategoryCreate(
        code=code,
        name_ar="التراث",
        name_en="Heritage",
        is_active=True,
    )


def test_create_normalizes_code_and_commits() -> None:
    service, session, repository = make_service()

    category = service.create_category(make_payload(" Heritage-Sites "))

    assert category.code == "heritage-sites"
    assert repository.categories[1] is category
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_create_rejects_code_conflict() -> None:
    service, session, repository = make_service()
    repository.code_conflict = True

    with pytest.raises(CategoryCodeConflictError):
        service.create_category(make_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_get_by_id_and_code_and_not_found() -> None:
    service, _, repository = make_service()
    category = Category(id=1, code="heritage", name_ar="تراث", name_en="Heritage")
    repository.categories[1] = category

    assert service.get_category_by_id(1) is category
    assert service.get_category_by_code(" HERITAGE ") is category
    with pytest.raises(CategoryNotFoundError):
        service.get_category_by_id(404)


def test_list_categories() -> None:
    service, _, repository = make_service()
    repository.categories[1] = Category(
        id=1,
        code="heritage",
        name_ar="تراث",
        name_en="Heritage",
        is_active=True,
    )

    items, total = service.list_categories(skip=0, limit=20, is_active=True)

    assert len(items) == 1
    assert total == 1


def test_update_checks_code_and_commits() -> None:
    service, session, repository = make_service()
    category = Category(id=1, code="heritage", name_ar="تراث", name_en="Heritage")
    repository.categories[1] = category

    updated = service.update_category(
        1,
        CategoryUpdate(code="culture", name_en="Culture"),
    )

    assert updated.code == "culture"
    assert updated.name_en == "Culture"
    session.commit.assert_called_once_with()


def test_delete_is_hard_delete_and_commits() -> None:
    service, session, repository = make_service()
    category = Category(id=1, code="heritage", name_ar="تراث", name_en="Heritage")
    repository.categories[1] = category

    service.delete_category(1)

    assert repository.deleted is category
    assert repository.categories == {}
    session.commit.assert_called_once_with()


def test_integrity_error_rolls_back() -> None:
    service, session, repository = make_service()
    repository.flush_error = IntegrityError("insert", {}, Exception("duplicate"))

    with pytest.raises(CategoryIntegrityError):
        service.create_category(make_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_sqlalchemy_error_rolls_back() -> None:
    service, session, repository = make_service()
    repository.flush_error = SQLAlchemyError("database unavailable")

    with pytest.raises(CategoryPersistenceError):
        service.create_category(make_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_read_sqlalchemy_error_becomes_persistence_error() -> None:
    service, session, repository = make_service()
    repository.read_error = SQLAlchemyError("database unavailable")

    with pytest.raises(CategoryPersistenceError):
        service.get_category_by_id(1)

    session.rollback.assert_not_called()
