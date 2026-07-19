from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import DestinationNotFoundError, ReviewIntegrityError, ReviewNotFoundError, ReviewPersistenceError, ReviewRatingError
from app.models.review import Review, ReviewStatus
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.review import ReviewService


class FakeReviewRepository:
    def __init__(self) -> None:
        self.reviews: dict[int, Review] = {}
        self.destinations = {7}
        self.flush_error: Exception | None = None
        self.read_error: Exception | None = None
        self.deleted: Review | None = None

    def get_by_id(self, review_id: int) -> Review | None:
        if self.read_error: raise self.read_error
        return self.reviews.get(review_id)
    def get_approved_by_id(self, review_id: int) -> Review | None:
        review = self.get_by_id(review_id)
        return review if review and review.status == ReviewStatus.APPROVED else None
    def destination_exists(self, destination_id: int) -> bool: return destination_id in self.destinations
    def list(self, **_: object) -> list[Review]:
        if self.read_error: raise self.read_error
        return list(self.reviews.values())
    def count(self, **_: object) -> int:
        if self.read_error: raise self.read_error
        return len(self.reviews)
    def list_approved_by_destination(self, *, destination_id: int, skip: int, limit: int) -> list[Review]:
        return [item for item in self.reviews.values() if item.destination_id == destination_id and item.status == ReviewStatus.APPROVED][skip:skip + limit]
    def count_approved_by_destination(self, destination_id: int) -> int: return len(self.list_approved_by_destination(destination_id=destination_id, skip=0, limit=1000))
    def add(self, review: Review) -> None:
        review.id = max(self.reviews, default=0) + 1
        self.reviews[review.id] = review
    def delete(self, review: Review) -> None:
        self.deleted = review
        self.reviews.pop(review.id, None)
    def flush(self) -> None:
        if self.flush_error: raise self.flush_error
    def refresh(self, review: Review) -> None: pass


def make_service() -> tuple[ReviewService, MagicMock, FakeReviewRepository]:
    session = MagicMock(); session.is_active = True
    repository = FakeReviewRepository()
    return ReviewService(session, repository), session, repository  # type: ignore[arg-type]


def payload(rating: int = 5) -> ReviewCreate:
    return ReviewCreate(destination_id=7, reviewer_name="Visitor", reviewer_email="visitor@example.com", rating=rating, title="Wonderful", body="Excellent destination")


def test_create_defaults_pending_unverified_and_commits() -> None:
    service, session, _ = make_service()
    review = service.create_review(payload())
    assert review.status == ReviewStatus.PENDING and review.is_verified is False
    session.commit.assert_called_once_with(); session.rollback.assert_not_called()


def test_create_destination_not_found_rolls_back() -> None:
    service, session, repository = make_service(); repository.destinations.clear()
    with pytest.raises(DestinationNotFoundError): service.create_review(payload())
    session.rollback.assert_called_once_with()


def test_service_rating_validation() -> None:
    service, session, _ = make_service()
    invalid = MagicMock(); invalid.rating = 6; invalid.destination_id = 7
    with pytest.raises(ReviewRatingError): service.create_review(invalid)
    session.rollback.assert_called_once_with()


def test_update_and_delete() -> None:
    service, session, repository = make_service()
    review = Review(id=1, destination_id=7, rating=4, body="Good", status=ReviewStatus.PENDING, is_verified=False)
    repository.reviews[1] = review
    updated = service.update_review(1, ReviewUpdate(rating=5, body="Excellent", is_verified=True))
    assert updated.rating == 5 and updated.is_verified is True
    service.delete_review(1)
    assert repository.deleted is review and repository.reviews == {}
    assert session.commit.call_count == 2


@pytest.mark.parametrize("status", [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.HIDDEN])
def test_moderation_and_published_at_behavior(status: ReviewStatus) -> None:
    service, session, repository = make_service()
    review = Review(id=1, destination_id=7, rating=5, body="Great", status=ReviewStatus.PENDING)
    repository.reviews[1] = review
    result = service.moderate_review(1, status)
    assert result.status == status
    assert (result.published_at is not None) is (status == ReviewStatus.APPROVED)
    session.commit.assert_called_once_with()


def test_approval_preserves_existing_published_at() -> None:
    from datetime import UTC, datetime
    service, _, repository = make_service(); published = datetime.now(UTC)
    review = Review(id=1, destination_id=7, rating=5, body="Great", status=ReviewStatus.APPROVED, published_at=published)
    repository.reviews[1] = review
    assert service.moderate_review(1, ReviewStatus.APPROVED).published_at is published


def test_public_reads_show_only_approved_and_not_found() -> None:
    service, _, repository = make_service()
    repository.reviews[1] = Review(id=1, destination_id=7, rating=5, body="Approved", status=ReviewStatus.APPROVED)
    repository.reviews[2] = Review(id=2, destination_id=7, rating=3, body="Pending", status=ReviewStatus.PENDING)
    items, total = service.list_approved_by_destination(7, skip=0, limit=20)
    assert [item.id for item in items] == [1] and total == 1
    assert service.get_approved_review(1).id == 1
    with pytest.raises(ReviewNotFoundError): service.get_approved_review(2)


def test_not_found_update_and_delete() -> None:
    service, session, _ = make_service()
    with pytest.raises(ReviewNotFoundError): service.update_review(404, ReviewUpdate(body="Missing"))
    with pytest.raises(ReviewNotFoundError): service.delete_review(404)
    assert session.rollback.call_count == 2


@pytest.mark.parametrize("error, expected", [(IntegrityError("x", {}, Exception()), ReviewIntegrityError), (SQLAlchemyError("x"), ReviewPersistenceError)])
def test_write_errors_rollback(error: Exception, expected: type[Exception]) -> None:
    service, session, repository = make_service(); repository.flush_error = error
    with pytest.raises(expected): service.create_review(payload())
    session.rollback.assert_called_once_with(); session.commit.assert_not_called()


def test_read_sqlalchemy_error_becomes_persistence_error() -> None:
    service, session, repository = make_service(); repository.read_error = SQLAlchemyError("down")
    with pytest.raises(ReviewPersistenceError): service.list_reviews(skip=0, limit=20, destination_id=None, status=None, rating=None, is_verified=None, sort_by="id", sort_order="asc")
    session.rollback.assert_not_called()
