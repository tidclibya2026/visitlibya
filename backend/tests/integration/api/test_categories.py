from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_category_service
from app.core.exceptions import (
    CategoryCodeConflictError,
    CategoryNotFoundError,
    CategoryPersistenceError,
)
from app.main import app
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def make_category(
    *,
    category_id: int = 1,
    code: str = "heritage",
    is_active: bool = True,
) -> Category:
    now = datetime.now(UTC)
    return Category(
        id=category_id,
        code=code,
        name_ar="التراث",
        name_en="Heritage",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


class FakeCategoryService:
    def __init__(self) -> None:
        self.category = make_category()
        self.list_arguments: dict[str, object] = {}
        self.deleted_id: int | None = None

    def list_categories(self, **arguments: object) -> tuple[list[Category], int]:
        self.list_arguments = arguments
        return [self.category], 1

    def get_category_by_code(self, code: str) -> Category:
        if code == "missing":
            raise CategoryNotFoundError()
        if code == "database-error":
            raise CategoryPersistenceError()
        return self.category

    def create_category(self, payload: CategoryCreate) -> Category:
        if payload.code == "duplicate":
            raise CategoryCodeConflictError()
        self.category = make_category(code=payload.code, is_active=payload.is_active)
        self.category.name_ar = payload.name_ar
        self.category.name_en = payload.name_en
        return self.category

    def update_category(self, category_id: int, payload: CategoryUpdate) -> Category:
        if category_id == 404:
            raise CategoryNotFoundError()
        if payload.code == "duplicate":
            raise CategoryCodeConflictError()
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(self.category, field, value)
        return self.category

    def delete_category(self, category_id: int) -> None:
        if category_id == 404:
            raise CategoryNotFoundError()
        self.deleted_id = category_id


def test_get_list_supports_pagination_and_active_filter() -> None:
    service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/categories",
                params={"skip": 5, "limit": 10, "is_active": True},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["skip"] == 5
    assert response.json()["limit"] == 10
    assert service.list_arguments == {"skip": 5, "limit": 10, "is_active": True}


def test_post_and_conflict_and_validation() -> None:
    service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: service
    payload = {"code": "culture", "name_ar": "الثقافة", "name_en": "Culture"}
    try:
        with TestClient(app) as client:
            created = client.post("/api/v1/categories", json=payload)
            conflict = client.post(
                "/api/v1/categories",
                json={**payload, "code": "duplicate"},
            )
            invalid = client.post(
                "/api/v1/categories",
                json={**payload, "code": "invalid code"},
            )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["code"] == "culture"
    assert conflict.status_code == 409
    assert invalid.status_code == 422


def test_get_by_code_and_errors() -> None:
    service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: service
    try:
        with TestClient(app) as client:
            found = client.get("/api/v1/categories/heritage")
            missing = client.get("/api/v1/categories/missing")
            failed = client.get("/api/v1/categories/database-error")
    finally:
        app.dependency_overrides.clear()

    assert found.status_code == 200
    assert missing.status_code == 404
    assert failed.status_code == 500
    assert failed.json() == {
        "detail": "Category service could not complete the request"
    }


def test_put_updates_and_handles_errors() -> None:
    service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: service
    try:
        with TestClient(app) as client:
            updated = client.put(
                "/api/v1/categories/1",
                json={"code": "culture", "is_active": False},
            )
            conflict = client.put(
                "/api/v1/categories/1",
                json={"code": "duplicate"},
            )
            missing = client.put(
                "/api/v1/categories/404",
                json={"name_en": "Missing"},
            )
            invalid = client.put("/api/v1/categories/1", json={"name_en": None})
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert updated.json()["code"] == "culture"
    assert updated.json()["is_active"] is False
    assert conflict.status_code == 409
    assert missing.status_code == 404
    assert invalid.status_code == 422


def test_delete_returns_204_and_404() -> None:
    service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: service
    try:
        with TestClient(app) as client:
            deleted = client.delete("/api/v1/categories/1")
            missing = client.delete("/api/v1/categories/404")
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert service.deleted_id == 1
    assert missing.status_code == 404
