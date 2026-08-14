from datetime import UTC, datetime

from fastapi.testclient import TestClient
from geoalchemy2.elements import WKTElement

from app.api.dependencies import get_destination_service, require_content_admin
from app.core.exceptions import (
    CategoryNotFoundError,
    DestinationIntegrityError,
    DestinationNotFoundError,
    DestinationPersistenceError,
    DestinationSlugConflictError,
)
from app.main import app
from app.models.destination import (
    Destination,
    DestinationStatus,
    DestinationTranslation,
)
from app.schemas.destination import DestinationCreate, DestinationUpdate


def make_destination(
    *,
    destination_id: int = 1,
    slug: str = "leptis-magna",
    language_code: str = "ar",
    name: str = "لبدة الكبرى",
) -> Destination:
    now = datetime.now(UTC)
    destination = Destination(
        id=destination_id,
        slug=slug,
        latitude=32.6389,
        longitude=14.2906,
        geometry=WKTElement("POINT(14.2906 32.6389)", srid=4326),
        status=DestinationStatus.DRAFT,
        priority_order=0,
        is_featured=False,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    destination.translations = [
        DestinationTranslation(
            id=destination_id,
            destination_id=destination_id,
            language_code=language_code,
            name=name,
            created_at=now,
            updated_at=now,
        )
    ]
    destination.category = None
    return destination


class FakeDestinationService:
    def __init__(self) -> None:
        self.destination = make_destination()
        self.list_arguments: dict[str, object] = {}
        self.created: Destination | None = None
        self.deleted_id: int | None = None

    def list_destinations(self, **arguments: object) -> tuple[list[Destination], int]:
        self.list_arguments = arguments
        return [self.destination], 1

    def list_public_destinations(self, **arguments: object) -> tuple[list[Destination], int]:
        self.list_arguments = arguments
        if self.destination.status == DestinationStatus.PUBLISHED and self.destination.is_active:
            return [self.destination], 1
        return [], 0

    def get_destination_by_slug(self, slug: str) -> Destination:
        if slug == "missing":
            raise DestinationNotFoundError()
        if slug == "database-error":
            raise DestinationPersistenceError()
        return self.destination

    def get_public_destination_by_slug(self, slug: str) -> Destination:
        destination = self.get_destination_by_slug(slug)
        if destination.status != DestinationStatus.PUBLISHED or not destination.is_active:
            raise DestinationNotFoundError()
        return destination

    def create_destination(self, payload: DestinationCreate) -> Destination:
        if payload.slug == "duplicate":
            raise DestinationSlugConflictError()
        if payload.category_id == 999:
            raise CategoryNotFoundError()
        if payload.slug == "integrity-conflict":
            raise DestinationIntegrityError()
        self.created = make_destination(slug=payload.slug)
        self.created.geometry = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})",
            srid=4326,
        )
        self.created.translations[0].language_code = payload.translations[0].language_code
        self.created.translations[0].name = payload.translations[0].name
        return self.created

    def update_destination(
        self,
        destination_id: int,
        payload: DestinationUpdate,
    ) -> Destination:
        if destination_id == 404:
            raise DestinationNotFoundError()
        if payload.slug == "duplicate":
            raise DestinationSlugConflictError()
        if payload.category_id == 999:
            raise CategoryNotFoundError()
        if payload.slug is not None:
            self.destination.slug = payload.slug
        if payload.translations is not None:
            self.destination.translations[0].language_code = (
                payload.translations[0].language_code
            )
            self.destination.translations[0].name = payload.translations[0].name
        return self.destination

    def delete_destination(self, destination_id: int) -> None:
        if destination_id == 404:
            raise DestinationNotFoundError()
        self.deleted_id = destination_id


def test_get_list_supports_pagination_and_filters() -> None:
    service = FakeDestinationService()
    service.destination.status = DestinationStatus.PUBLISHED
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/destinations",
                params={
                    "skip": 5,
                    "limit": 10,
                    "status": "published",
                    "category_id": 2,
                    "region": "Tripolitania",
                    "municipality": "Khoms",
                    "is_featured": True,
                    "is_active": True,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["skip"] == 5
    assert response.json()["limit"] == 10
    assert service.list_arguments["skip"] == 5
    assert service.list_arguments["region"] == "Tripolitania"
    assert "status" not in service.list_arguments
    assert "is_active" not in service.list_arguments


def test_get_by_slug_and_404() -> None:
    service = FakeDestinationService()
    service.destination.status = DestinationStatus.PUBLISHED
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            found = client.get("/api/v1/destinations/leptis-magna")
            missing = client.get("/api/v1/destinations/missing")
    finally:
        app.dependency_overrides.clear()

    assert found.status_code == 200
    assert found.json()["slug"] == "leptis-magna"
    assert found.json()["translations"][0]["name"] == "لبدة الكبرى"
    assert found.json()["latitude"] == 32.6389
    assert found.json()["longitude"] == 14.2906
    assert missing.status_code == 404


def test_public_list_rejects_non_public_filter_requests() -> None:
    service = FakeDestinationService()
    service.destination.status = DestinationStatus.PUBLISHED
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            draft = client.get("/api/v1/destinations", params={"status": "draft"})
            inactive = client.get("/api/v1/destinations", params={"is_active": False})
    finally:
        app.dependency_overrides.clear()
    assert draft.status_code == 200 and draft.json()["items"] == []
    assert inactive.status_code == 200 and inactive.json()["items"] == []


def test_public_list_hides_every_non_public_state() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            for destination_status in (
                DestinationStatus.DRAFT,
                DestinationStatus.UNDER_REVIEW,
                DestinationStatus.APPROVED,
                DestinationStatus.ARCHIVED,
            ):
                service.destination.status = destination_status
                service.destination.is_active = True
                response = client.get("/api/v1/destinations")
                assert response.status_code == 200
                assert response.json()["items"] == []
            service.destination.status = DestinationStatus.PUBLISHED
            service.destination.is_active = False
            response = client.get("/api/v1/destinations")
            assert response.json()["items"] == []
    finally:
        app.dependency_overrides.clear()


def test_public_detail_hides_unpublished_and_inactive_without_disclosure() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            for destination_status in (
                DestinationStatus.DRAFT,
                DestinationStatus.UNDER_REVIEW,
                DestinationStatus.APPROVED,
                DestinationStatus.ARCHIVED,
            ):
                service.destination.status = destination_status
                service.destination.is_active = True
                response = client.get("/api/v1/destinations/leptis-magna")
                assert response.status_code == 404
                assert response.json() == {"detail": "Destination not found"}
            service.destination.status = DestinationStatus.PUBLISHED
            service.destination.is_active = False
            response = client.get("/api/v1/destinations/leptis-magna")
            assert response.status_code == 404
            assert response.json() == {"detail": "Destination not found"}
    finally:
        app.dependency_overrides.clear()


def test_admin_reads_preserve_draft_access_and_coordinates() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    try:
        with TestClient(app) as client:
            listed = client.get("/api/v1/destinations/admin", params={"status": "draft"})
            detail = client.get("/api/v1/destinations/admin/leptis-magna")
    finally:
        app.dependency_overrides.clear()
    assert listed.status_code == 200 and listed.json()["items"][0]["status"] == "draft"
    assert service.list_arguments["status"] == DestinationStatus.DRAFT
    assert detail.status_code == 200
    assert detail.json()["latitude"] == 32.6389
    assert detail.json()["longitude"] == 14.2906


def test_admin_destination_reads_require_authentication() -> None:
    with TestClient(app) as client:
        listed = client.get("/api/v1/destinations/admin")
        detail = client.get("/api/v1/destinations/admin/leptis-magna")
    assert listed.status_code == 401
    assert detail.status_code == 401


def test_post_translations_geometry_and_conflicts() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    payload = {
        "slug": "sabratha",
        "category_id": 1,
        "latitude": 32.8053,
        "longitude": 12.4853,
        "translations": [{"language_code": "EN", "name": "Sabratha"}],
    }
    try:
        with TestClient(app) as client:
            created = client.post("/api/v1/destinations", json=payload)
            conflict = client.post(
                "/api/v1/destinations",
                json={**payload, "slug": "duplicate"},
            )
            category_error = client.post(
                "/api/v1/destinations",
                json={**payload, "slug": "invalid-category", "category_id": 999},
            )
            validation_error = client.post(
                "/api/v1/destinations",
                json={**payload, "slug": "invalid-coordinates", "longitude": None},
            )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["translations"][0]["language_code"] == "en"
    assert service.created is not None
    assert service.created.geometry.srid == 4326
    assert str(service.created.geometry) == "POINT(12.4853 32.8053)"
    assert conflict.status_code == 409
    assert category_error.status_code == 422
    assert validation_error.status_code == 422


def test_put_updates_destination_and_validates_category() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    try:
        with TestClient(app) as client:
            updated = client.put(
                "/api/v1/destinations/1",
                json={
                    "slug": "leptis-magna-updated",
                    "translations": [
                        {"language_code": "en", "name": "Leptis Magna"}
                    ],
                },
            )
            category_error = client.put(
                "/api/v1/destinations/1",
                json={"category_id": 999},
            )
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert updated.json()["slug"] == "leptis-magna-updated"
    assert updated.json()["translations"][0]["language_code"] == "en"
    assert category_error.status_code == 422


def test_delete_returns_204_and_missing_returns_404() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    try:
        with TestClient(app) as client:
            deleted = client.delete("/api/v1/destinations/1")
            missing = client.delete("/api/v1/destinations/404")
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert service.deleted_id == 1
    assert missing.status_code == 404


def test_persistence_error_returns_generic_500() -> None:
    service = FakeDestinationService()
    app.dependency_overrides[get_destination_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/destinations/database-error")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Destination service could not complete the request"
    }


def test_client_approval_fields_are_rejected_and_never_projected_publicly() -> None:
    service = FakeDestinationService()
    service.destination.status = DestinationStatus.PUBLISHED
    app.dependency_overrides[get_destination_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    payload = {"slug": "synthetic", "translations": [{"language_code": "en", "name": "Synthetic"}]}
    try:
        with TestClient(app) as client:
            direct = client.post("/api/v1/destinations", json={**payload, "publication_approved": True})
            decision = client.post("/api/v1/destinations", json={**payload, "institutional_decision": "APPROVED"})
            public = client.get("/api/v1/destinations/leptis-magna")
    finally:
        app.dependency_overrides.clear()
    assert direct.status_code == 422 and decision.status_code == 422
    assert public.status_code == 200
    assert not ({"publication_approved", "institutional_decision", "evidence_reference", "actor_id"} & public.json().keys())
