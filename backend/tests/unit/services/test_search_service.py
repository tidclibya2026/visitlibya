from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import SearchPersistenceError, SearchValidationError
from app.models.category import Category
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.repositories.search import SearchResultRow
from app.schemas.search import SearchDestinationItem, SearchFilters
from app.services.search import SearchService


class FakeSearchRepository:
    def __init__(self) -> None:
        self.arguments: dict[str, object] = {}; self.error: Exception | None = None
        category = Category(id=3, code="heritage", name_ar="التراث", name_en="Heritage")
        destination = Destination(id=1, slug="leptis-magna", status=DestinationStatus.PUBLISHED, municipality="Al Khums", region="Tripolitania", latitude=32.6389, longitude=14.2906, is_featured=True, is_active=True)
        destination.category = category
        destination.translations = [DestinationTranslation(language_code="ar", name="لبدة الكبرى", short_description="مدينة أثرية"), DestinationTranslation(language_code="en", name="Leptis Magna", short_description="Ancient city")]
        self.rows = [SearchResultRow(destination, 4.5, 2, "/media/leptis.jpg")]

    def search(self, **arguments: object) -> tuple[list[SearchResultRow], int]:
        if self.error is not None: raise self.error
        self.arguments = arguments
        return self.rows, len(self.rows)


def make_service() -> tuple[SearchService, MagicMock, FakeSearchRepository]:
    session = MagicMock(); session.is_active = True
    repository = FakeSearchRepository()
    return SearchService(session, repository), session, repository  # type: ignore[arg-type]


def test_valid_search_maps_results_and_pagination() -> None:
    service, session, repository = make_service()
    response = service.search_destinations(filters=SearchFilters(q="Leptis"), page=2, page_size=10, sort_by="average_rating", sort_order="desc")
    item = response.items[0]
    assert response.page == 2 and response.page_size == 10 and response.total == 1
    assert repository.arguments["offset"] == 10 and repository.arguments["limit"] == 10
    assert item.name_ar == "لبدة الكبرى" and item.name_en == "Leptis Magna"
    assert item.category is not None and item.category.code == "heritage"
    assert item.average_rating == 4.5 and item.reviews_count == 2 and item.primary_media_url == "/media/leptis.jpg"
    assert item.latitude == 32.6389 and item.longitude == 14.2906
    session.commit.assert_not_called(); session.rollback.assert_not_called()


def test_search_coordinates_require_a_complete_pair() -> None:
    with pytest.raises(ValueError, match="must be provided together"):
        SearchDestinationItem(
            id=1, slug="leptis-magna", name_ar=None, name_en="Leptis Magna",
            short_description_ar=None, short_description_en=None,
            municipality=None, region=None, latitude=32.6389, longitude=None,
            category=None, primary_media_url=None, is_featured=False,
            average_rating=None, reviews_count=0,
        )


@pytest.mark.parametrize("page,page_size", [(0, 20), (1, 0), (1, 101)])
def test_pagination_validation(page: int, page_size: int) -> None:
    service, _, _ = make_service()
    with pytest.raises(SearchValidationError):
        service.search_destinations(filters=SearchFilters(), page=page, page_size=page_size, sort_by="name", sort_order="asc")


def test_rating_range_and_sort_validation() -> None:
    service, _, _ = make_service()
    invalid_range = SearchFilters.model_construct(minimum_rating=5, maximum_rating=4)
    with pytest.raises(SearchValidationError): service.search_destinations(filters=invalid_range, page=1, page_size=20, sort_by="name", sort_order="asc")
    with pytest.raises(SearchValidationError): service.search_destinations(filters=SearchFilters(), page=1, page_size=20, sort_by="unsafe", sort_order="asc")  # type: ignore[arg-type]
    with pytest.raises(SearchValidationError): service.search_destinations(filters=SearchFilters(), page=1, page_size=20, sort_by="name", sort_order="sideways")  # type: ignore[arg-type]
    for invalid_rating in (0, 6):
        invalid = SearchFilters.model_construct(
            minimum_rating=invalid_rating,
            maximum_rating=None,
        )
        with pytest.raises(SearchValidationError):
            service.search_destinations(
                filters=invalid,
                page=1,
                page_size=20,
                sort_by="name",
                sort_order="asc",
            )


def test_repository_error_becomes_persistence_error_without_healthy_rollback() -> None:
    service, session, repository = make_service(); repository.error = SQLAlchemyError("down")
    with pytest.raises(SearchPersistenceError): service.search_destinations(filters=SearchFilters(), page=1, page_size=20, sort_by="name", sort_order="asc")
    session.rollback.assert_not_called()


def test_repository_error_rolls_back_failed_session() -> None:
    service, session, repository = make_service(); repository.error = SQLAlchemyError("down"); session.is_active = False
    with pytest.raises(SearchPersistenceError): service.search_destinations(filters=SearchFilters(), page=1, page_size=20, sort_by="name", sort_order="asc")
    session.rollback.assert_called_once_with()
