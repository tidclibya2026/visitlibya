from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DestinationNotFoundError,
    ReviewError,
    ReviewIntegrityError,
    ReviewNotFoundError,
    ReviewPersistenceError,
    ReviewRatingError,
)
from app.models.review import Review, ReviewStatus
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewSortField, ReviewSortOrder, ReviewUpdate


class ReviewService:
    def __init__(self, session: Session, repository: ReviewRepository | None = None) -> None:
        self.session = session
        self.repository = repository or ReviewRepository(session)

    def list_approved_by_destination(self, destination_id: int, *, skip: int, limit: int) -> tuple[Sequence[Review], int]:
        try:
            items = self.repository.list_approved_by_destination(destination_id=destination_id, skip=skip, limit=limit)
            total = self.repository.count_approved_by_destination(destination_id)
            return items, total
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise ReviewPersistenceError() from exc

    def get_approved_review(self, review_id: int) -> Review:
        try:
            review = self.repository.get_approved_by_id(review_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise ReviewPersistenceError() from exc
        if review is None:
            raise ReviewNotFoundError()
        return review

    def list_reviews(self, *, skip: int, limit: int, destination_id: int | None, status: ReviewStatus | None, rating: int | None, is_verified: bool | None, sort_by: ReviewSortField, sort_order: ReviewSortOrder) -> tuple[Sequence[Review], int]:
        try:
            filters = {"destination_id": destination_id, "status": status, "rating": rating, "is_verified": is_verified}
            total = self.repository.count(**filters)
            items = self.repository.list(skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, **filters)
            return items, total
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise ReviewPersistenceError() from exc

    def create_review(self, payload: ReviewCreate) -> Review:
        try:
            self._ensure_rating(payload.rating)
            if not self.repository.destination_exists(payload.destination_id):
                raise DestinationNotFoundError()
            review = Review(**payload.model_dump(), status=ReviewStatus.PENDING, is_verified=False)
            self.repository.add(review)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(review)
            return review
        except (ReviewError, DestinationNotFoundError):
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ReviewPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_review(self, review_id: int, payload: ReviewUpdate) -> Review:
        try:
            review = self._get_required_review(review_id)
            values = payload.model_dump(exclude_unset=True)
            if "rating" in values:
                self._ensure_rating(values["rating"])
            for field, value in values.items():
                setattr(review, field, value)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(review)
            return review
        except ReviewError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ReviewPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def moderate_review(self, review_id: int, status: ReviewStatus) -> Review:
        try:
            review = self._get_required_review(review_id)
            review.status = status
            if status == ReviewStatus.APPROVED:
                review.published_at = review.published_at or datetime.now(UTC)
            else:
                review.published_at = None
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(review)
            return review
        except ReviewError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ReviewPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def delete_review(self, review_id: int) -> None:
        try:
            review = self._get_required_review(review_id)
            self.repository.delete(review)
            self.repository.flush()
            self.session.commit()
        except ReviewError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ReviewPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def _get_required_review(self, review_id: int) -> Review:
        review = self.repository.get_by_id(review_id)
        if review is None:
            raise ReviewNotFoundError()
        return review

    @staticmethod
    def _ensure_rating(rating: int) -> None:
        if not 1 <= rating <= 5:
            raise ReviewRatingError()

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
