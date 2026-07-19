from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_media_service
from app.core.exceptions import DestinationMediaConflictError, DestinationMediaNotFoundError, MediaAssetNotFoundError, MediaAssetPathConflictError, MediaAssetPersistenceError
from app.main import app
from app.models.media import DestinationMedia, MediaAsset


def media_asset() -> MediaAsset:
    now = datetime.now(UTC)
    return MediaAsset(id=1, file_name="leptis.jpg", file_path="/media/leptis.jpg", public_url="/media/leptis.jpg", mime_type="image/jpeg", file_size=100, width=1200, height=800, copyright_owner="Visit Libya", is_active=True, destination_links=[], created_at=now, updated_at=now)


class FakeMediaService:
    def __init__(self) -> None:
        self.media = media_asset(); self.link: DestinationMedia | None = None; self.arguments: dict[str, object] = {}
    def list_media(self, **arguments: object) -> tuple[list[MediaAsset], int]: self.arguments = arguments; return [self.media], 1
    def get_media(self, media_id: int) -> MediaAsset:
        if media_id == 404: raise MediaAssetNotFoundError()
        if media_id == 500: raise MediaAssetPersistenceError()
        return self.media
    def create_media(self, payload: object) -> MediaAsset:
        if getattr(payload, "file_path") == "/duplicate.jpg": raise MediaAssetPathConflictError()
        return self.media
    def update_media(self, media_id: int, payload: object) -> MediaAsset:
        if media_id == 404: raise MediaAssetNotFoundError()
        for key, value in payload.model_dump(exclude_unset=True).items(): setattr(self.media, key, value)
        return self.media
    def delete_media(self, media_id: int) -> None:
        if media_id == 404: raise MediaAssetNotFoundError()
    def associate_destination(self, media_id: int, destination_id: int, payload: object) -> DestinationMedia:
        if destination_id == 409: raise DestinationMediaConflictError()
        now = datetime.now(UTC); self.link = DestinationMedia(id=1, destination_id=destination_id, media_id=media_id, sort_order=getattr(payload, "sort_order"), is_primary=getattr(payload, "is_primary"), created_at=now, updated_at=now); return self.link
    def update_destination_link(self, media_id: int, destination_id: int, payload: object) -> DestinationMedia:
        if self.link is None: raise DestinationMediaNotFoundError()
        for key, value in payload.model_dump(exclude_unset=True).items(): setattr(self.link, key, value)
        return self.link
    def remove_destination(self, media_id: int, destination_id: int) -> None:
        if self.link is None: raise DestinationMediaNotFoundError()
        self.link = None


def test_media_crud_pagination_filters_ordering_and_errors() -> None:
    service = FakeMediaService(); app.dependency_overrides[get_media_service] = lambda: service
    body = {"file_name": "leptis.jpg", "file_path": "/media/leptis.jpg", "mime_type": "image/jpeg"}
    try:
        with TestClient(app) as client:
            listed = client.get("/api/v1/media", params={"skip": 5, "limit": 10, "mime_type": "image/jpeg", "destination_id": 7, "is_primary": True, "sort_by": "created_at", "sort_order": "desc"})
            created = client.post("/api/v1/media", json=body)
            found = client.get("/api/v1/media/1")
            updated = client.put("/api/v1/media/1", json={"caption_en": "Updated"})
            deleted = client.delete("/api/v1/media/1")
            missing = client.get("/api/v1/media/404")
            conflict = client.post("/api/v1/media", json={**body, "file_path": "/duplicate.jpg"})
            failed = client.get("/api/v1/media/500")
            invalid = client.post("/api/v1/media", json={**body, "file_size": -1})
    finally: app.dependency_overrides.clear()
    assert listed.status_code == 200 and listed.json()["skip"] == 5
    assert service.arguments["sort_order"] == "desc" and service.arguments["is_primary"] is True
    assert created.status_code == 201 and found.status_code == 200 and updated.status_code == 200 and deleted.status_code == 204
    assert missing.status_code == 404 and conflict.status_code == 409 and invalid.status_code == 422
    assert failed.status_code == 500 and failed.json()["detail"] == "Media service could not complete the request"


def test_destination_association_primary_update_and_remove() -> None:
    service = FakeMediaService(); app.dependency_overrides[get_media_service] = lambda: service
    try:
        with TestClient(app) as client:
            linked = client.post("/api/v1/media/1/destinations/7", json={"sort_order": 2, "is_primary": True})
            primary = client.put("/api/v1/media/1/destinations/7", json={"is_primary": True, "sort_order": 1})
            removed = client.delete("/api/v1/media/1/destinations/7")
            missing = client.delete("/api/v1/media/1/destinations/7")
            conflict = client.post("/api/v1/media/1/destinations/409", json={})
    finally: app.dependency_overrides.clear()
    assert linked.status_code == 201 and linked.json()["is_primary"] is True
    assert primary.status_code == 200 and primary.json()["sort_order"] == 1
    assert removed.status_code == 204 and missing.status_code == 404 and conflict.status_code == 409
