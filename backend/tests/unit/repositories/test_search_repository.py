from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.models.review import ReviewStatus
from app.repositories.search import SearchRepository
from app.schemas.search import SearchFilters


def make_destination(destination_id: int = 1) -> Destination:
    destination = Destination(id=destination_id, slug="leptis-magna", status=DestinationStatus.PUBLISHED, municipality="Al Khums", region="Tripolitania", is_featured=True, is_active=True)
    destination.translations = [DestinationTranslation(language_code="en", name="Leptis Magna")]
    return destination


def make_repository_row(*, average_rating: Decimal | None = Decimal("4.5"), reviews_count: int = 2) -> tuple[SearchRepository, MagicMock, Destination]:
    destination = make_destination()
    result = MagicMock(); result.all.return_value = [(destination, average_rating, reviews_count, "/media/leptis.jpg")]
    session = MagicMock(); session.execute.return_value = result; session.scalar.return_value = 1
    return SearchRepository(session), session, destination


def test_text_search_and_all_filters_build_one_aggregate_query() -> None:
    repository, session, destination = make_repository_row()
    filters = SearchFilters(q="Leptis", category_id=3, city="Al Khums", region="Tripolitania", is_featured=True, minimum_rating=4, maximum_rating=5)
    rows, total = repository.search(filters=filters, offset=10, limit=5, sort_by="average_rating", sort_order="desc")
    assert rows[0].destination is destination and rows[0].average_rating == 4.5
    assert rows[0].reviews_count == 2 and total == 1
    statement = session.execute.call_args.args[0]; sql = str(statement)
    assert "approved_review_aggregate" in sql and "reviews.status" in sql
    assert "EXISTS" in sql and "destinations.category_id" in sql
    assert "destinations.municipality" in sql and "destinations.region" in sql
    assert "destinations.is_featured" in sql and "average_rating" in sql and "DESC NULLS LAST" in sql
    assert "row_number() OVER" in sql and "media_rank" in sql
    assert len(statement._with_options) == 2
    count_sql = str(session.scalar.call_args.args[0])
    assert "destinations.category_id" in count_sql
    assert "destinations.municipality" in count_sql
    assert "average_rating" in count_sql
    session.execute.assert_called_once(); session.scalar.assert_called_once()


def test_public_filter_and_approved_reviews_are_always_enforced() -> None:
    repository, session, _ = make_repository_row()
    repository.search(filters=SearchFilters(), offset=0, limit=20, sort_by="created_at", sort_order="asc")
    statement = session.execute.call_args.args[0]
    sql = str(statement); parameters = statement.compile().params.values()
    assert "destinations.status" in sql and "destinations.is_active" in sql
    assert ReviewStatus.APPROVED in parameters and DestinationStatus.PUBLISHED in parameters
    assert ReviewStatus.PENDING not in parameters
    assert ReviewStatus.REJECTED not in parameters
    assert "status" not in SearchFilters.model_fields


def test_destination_without_reviews_has_null_average_and_zero_count() -> None:
    repository, _, destination = make_repository_row(average_rating=None, reviews_count=0)
    rows, _ = repository.search(filters=SearchFilters(), offset=0, limit=20, sort_by="reviews_count", sort_order="desc")
    assert rows[0].destination is destination
    assert rows[0].average_rating is None and rows[0].reviews_count == 0


def test_whitespace_query_behaves_as_no_text_query() -> None:
    repository, session, _ = make_repository_row()
    repository.search(
        filters=SearchFilters(q="   "),
        offset=0,
        limit=20,
        sort_by="name",
        sort_order="asc",
    )
    sql = str(session.execute.call_args.args[0])
    assert "EXISTS (SELECT destination_translations.id" not in sql


def test_pagination_count_name_sort_and_invalid_sort_protection() -> None:
    repository, session, _ = make_repository_row()
    repository.search(filters=SearchFilters(), offset=20, limit=10, sort_by="name", sort_order="asc")
    sql = str(session.execute.call_args.args[0])
    assert "min(destination_translations.name)" in sql and "LIMIT" in sql and "OFFSET" in sql
    assert "ORDER BY" in sql and "destinations.id" in sql
    count_sql = str(session.scalar.call_args.args[0])
    assert "count(distinct(destinations.id))" in count_sql
    with pytest.raises(KeyError):
        repository.search(filters=SearchFilters(), offset=0, limit=20, sort_by="unsafe_column", sort_order="asc")  # type: ignore[arg-type]


@pytest.mark.parametrize("sort_order", ["asc", "desc"])
def test_average_rating_sort_always_uses_nulls_last(
    sort_order: str,
) -> None:
    repository, session, _ = make_repository_row()
    repository.search(
        filters=SearchFilters(),
        offset=0,
        limit=20,
        sort_by="average_rating",
        sort_order=sort_order,  # type: ignore[arg-type]
    )
    sql = str(session.execute.call_args.args[0])
    assert "NULLS LAST" in sql
    assert (" ASC" in sql) is (sort_order == "asc")
    assert "destinations.id" in sql


def test_reviews_count_sort_uses_coalesce_and_stable_tie_breaker() -> None:
    repository, session, _ = make_repository_row()
    repository.search(
        filters=SearchFilters(),
        offset=0,
        limit=20,
        sort_by="reviews_count",
        sort_order="desc",
    )
    sql = str(session.execute.call_args.args[0])
    assert "coalesce(approved_review_aggregate.reviews_count" in sql
    assert "DESC" in sql and "destinations.id" in sql


def test_primary_media_ranking_is_one_row_per_destination() -> None:
    repository, session, _ = make_repository_row()
    repository.search(
        filters=SearchFilters(),
        offset=0,
        limit=20,
        sort_by="created_at",
        sort_order="desc",
    )
    sql = str(session.execute.call_args.args[0])
    assert "PARTITION BY destination_media.destination_id" in sql
    assert "destination_media.created_at DESC" in sql
    assert "destination_media.id DESC" in sql
    assert "media_rank" in sql
