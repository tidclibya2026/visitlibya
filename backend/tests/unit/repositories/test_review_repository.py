from unittest.mock import MagicMock

from app.models.review import Review, ReviewStatus
from app.repositories.review import ReviewRepository


def make_review() -> Review:
    return Review(id=1, destination_id=7, rating=5, body="Excellent", status=ReviewStatus.APPROVED)


def test_get_by_id_approved_and_destination_exists() -> None:
    review = make_review()
    session = MagicMock()
    session.scalar.side_effect = [review, review, 7]
    repository = ReviewRepository(session)

    assert repository.get_by_id(1) is review
    assert repository.get_approved_by_id(1) is review
    assert repository.destination_exists(7) is True


def test_list_and_count_apply_all_filters_and_safe_sorting() -> None:
    review = make_review()
    scalar_result = MagicMock()
    scalar_result.all.return_value = [review]
    session = MagicMock()
    session.scalars.return_value = scalar_result
    session.scalar.return_value = 1
    repository = ReviewRepository(session)

    items = repository.list(skip=0, limit=20, destination_id=7, status=ReviewStatus.APPROVED, rating=5, is_verified=True, sort_by="rating", sort_order="desc")
    total = repository.count(destination_id=7, status=ReviewStatus.APPROVED, rating=5, is_verified=True)

    assert list(items) == [review]
    assert total == 1
    statement = str(session.scalars.call_args.args[0])
    assert "destination_id" in statement and "status" in statement
    assert "rating" in statement and "is_verified" in statement
    assert "DESC" in statement


def test_approved_reviews_by_destination() -> None:
    review = make_review()
    scalar_result = MagicMock()
    scalar_result.all.return_value = [review]
    session = MagicMock()
    session.scalars.return_value = scalar_result
    session.scalar.return_value = 1
    repository = ReviewRepository(session)

    assert list(repository.list_approved_by_destination(destination_id=7, skip=0, limit=10)) == [review]
    assert repository.count_approved_by_destination(7) == 1
    parameters = session.scalars.call_args.args[0].compile().params
    assert ReviewStatus.APPROVED in parameters.values()


def test_add_delete_and_write_helpers_do_not_manage_transactions() -> None:
    review = make_review()
    session = MagicMock()
    repository = ReviewRepository(session)

    repository.add(review)
    repository.flush()
    repository.refresh(review)
    repository.delete(review)

    session.add.assert_called_once_with(review)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(review)
    session.delete.assert_called_once_with(review)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
