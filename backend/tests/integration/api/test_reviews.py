from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_review_service, require_content_admin
from app.core.exceptions import ReviewIntegrityError, ReviewNotFoundError, ReviewPersistenceError
from app.main import app
from app.models.review import Review, ReviewStatus


def make_review(review_id: int = 1, status: ReviewStatus = ReviewStatus.PENDING) -> Review:
    now = datetime.now(UTC)
    return Review(id=review_id, destination_id=7, user_id=None, reviewer_name="Visitor", reviewer_email="visitor@example.com", rating=5, title="Wonderful", body="Excellent destination", status=status, is_verified=False, published_at=now if status == ReviewStatus.APPROVED else None, created_at=now, updated_at=now)


class FakeReviewService:
    def __init__(self) -> None:
        self.reviews = {1: make_review(1, ReviewStatus.APPROVED), 2: make_review(2)}
        self.arguments: dict[str, object] = {}
    def create_review(self, payload: object) -> Review:
        destination_id = getattr(payload, "destination_id")
        if destination_id == 409: raise ReviewIntegrityError()
        if destination_id == 500: raise ReviewPersistenceError()
        return make_review(3)
    def list_approved_by_destination(self, destination_id: int, *, skip: int, limit: int) -> tuple[list[Review], int]:
        items = [item for item in self.reviews.values() if item.destination_id == destination_id and item.status == ReviewStatus.APPROVED]
        return items[skip:skip + limit], len(items)
    def get_approved_review(self, review_id: int) -> Review:
        review = self.reviews.get(review_id)
        if review is None or review.status != ReviewStatus.APPROVED: raise ReviewNotFoundError()
        return review
    def list_reviews(self, **arguments: object) -> tuple[list[Review], int]:
        self.arguments = arguments
        items = list(self.reviews.values())
        return items, len(items)
    def update_review(self, review_id: int, payload: object) -> Review:
        if review_id == 404: raise ReviewNotFoundError()
        review = self.reviews[review_id]
        for field, value in payload.model_dump(exclude_unset=True).items(): setattr(review, field, value)
        return review
    def moderate_review(self, review_id: int, status: ReviewStatus) -> Review:
        if review_id == 404: raise ReviewNotFoundError()
        review = self.reviews[review_id]; review.status = status
        review.published_at = datetime.now(UTC) if status == ReviewStatus.APPROVED else None
        return review
    def delete_review(self, review_id: int) -> None:
        if review_id not in self.reviews: raise ReviewNotFoundError()
        del self.reviews[review_id]


def review_payload(destination_id: int = 7) -> dict[str, object]:
    return {"destination_id": destination_id, "reviewer_name": "Visitor", "reviewer_email": "visitor@example.com", "rating": 5, "title": "Wonderful", "body": "Excellent destination"}


def test_public_create_list_get_and_errors() -> None:
    service = FakeReviewService(); app.dependency_overrides[get_review_service] = lambda: service
    try:
        with TestClient(app) as client:
            created = client.post("/api/v1/reviews", json=review_payload())
            listed = client.get("/api/v1/reviews/destinations/7", params={"skip": 0, "limit": 10})
            approved = client.get("/api/v1/reviews/1")
            pending = client.get("/api/v1/reviews/2")
            conflict = client.post("/api/v1/reviews", json=review_payload(409))
            failed = client.post("/api/v1/reviews", json=review_payload(500))
            invalid = client.post("/api/v1/reviews", json={**review_payload(), "rating": 6})
    finally: app.dependency_overrides.clear()
    assert created.status_code == 201 and created.json()["status"] == "pending"
    assert listed.status_code == 200 and listed.json()["total"] == 1
    assert [item["id"] for item in listed.json()["items"]] == [1]
    assert approved.status_code == 200 and pending.status_code == 404
    assert conflict.status_code == 409 and invalid.status_code == 422
    assert failed.status_code == 500 and failed.json()["detail"] == "Review service could not complete the request"


def test_admin_list_pagination_filters_and_update() -> None:
    service = FakeReviewService(); app.dependency_overrides[get_review_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    try:
        with TestClient(app) as client:
            listed = client.get("/api/v1/reviews/admin", params={"skip": 5, "limit": 10, "destination_id": 7, "status": "pending", "rating": 5, "is_verified": False, "sort_by": "rating", "sort_order": "asc"})
            updated = client.put("/api/v1/reviews/admin/1", json={"body": "Updated", "is_verified": True})
            missing = client.put("/api/v1/reviews/admin/404", json={"body": "Missing"})
    finally: app.dependency_overrides.clear()
    assert listed.status_code == 200 and listed.json()["skip"] == 5
    assert service.arguments["status"] == ReviewStatus.PENDING and service.arguments["rating"] == 5
    assert updated.status_code == 200 and updated.json()["body"] == "Updated" and updated.json()["is_verified"] is True
    assert missing.status_code == 404


def test_admin_approve_reject_hide_delete_and_404() -> None:
    service = FakeReviewService(); app.dependency_overrides[get_review_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: object()
    try:
        with TestClient(app) as client:
            approved = client.patch("/api/v1/reviews/admin/2/status", json={"status": "approved"})
            rejected = client.patch("/api/v1/reviews/admin/2/status", json={"status": "rejected"})
            hidden = client.patch("/api/v1/reviews/admin/2/status", json={"status": "hidden"})
            invalid = client.patch("/api/v1/reviews/admin/2/status", json={"status": "invalid"})
            deleted = client.delete("/api/v1/reviews/admin/2")
            missing = client.delete("/api/v1/reviews/admin/404")
    finally: app.dependency_overrides.clear()
    assert approved.status_code == 200 and approved.json()["published_at"] is not None
    assert rejected.status_code == 200 and rejected.json()["published_at"] is None
    assert hidden.status_code == 200 and hidden.json()["status"] == "hidden"
    assert invalid.status_code == 422 and deleted.status_code == 204 and missing.status_code == 404
