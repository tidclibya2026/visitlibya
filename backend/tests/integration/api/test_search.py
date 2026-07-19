from fastapi.testclient import TestClient

from app.api.dependencies import get_search_service
from app.core.exceptions import SearchPersistenceError
from app.main import app
from app.schemas.search import SearchDestinationItem, SearchDestinationResponse


class FakeSearchService:
    def __init__(self) -> None: self.arguments: dict[str, object] = {}
    def search_destinations(self, **arguments: object) -> SearchDestinationResponse:
        self.arguments = arguments; filters = arguments["filters"]
        if getattr(filters, "q") == "database-error": raise SearchPersistenceError()
        items = [] if getattr(filters, "q") == "empty" else [SearchDestinationItem(id=1, slug="leptis-magna", name_ar="لبدة الكبرى", name_en="Leptis Magna", short_description_ar="مدينة أثرية", short_description_en="Ancient city", municipality="Al Khums", region="Tripolitania", category=None, primary_media_url="/media/leptis.jpg", is_featured=True, average_rating=4.5, reviews_count=2)]
        return SearchDestinationResponse.create(items=items, total=len(items), page=arguments["page"], page_size=arguments["page_size"])


def test_search_query_filters_pagination_and_sorting() -> None:
    service = FakeSearchService(); app.dependency_overrides[get_search_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/search/destinations", params={"q": "Leptis", "category_id": 3, "city": "Al Khums", "region": "Tripolitania", "is_featured": True, "minimum_rating": 4, "maximum_rating": 5, "page": 2, "page_size": 10, "sort_by": "average_rating", "sort_order": "desc"})
    finally: app.dependency_overrides.clear()
    assert response.status_code == 200 and response.json()["items"][0]["reviews_count"] == 2
    filters = service.arguments["filters"]
    assert filters.q == "Leptis" and filters.category_id == 3 and filters.city == "Al Khums"
    assert filters.is_featured is True and filters.minimum_rating == 4
    assert service.arguments["page"] == 2 and service.arguments["sort_order"] == "desc"


def test_empty_result_validation_and_generic_500() -> None:
    service = FakeSearchService(); app.dependency_overrides[get_search_service] = lambda: service
    try:
        with TestClient(app) as client:
            empty = client.get("/api/v1/search/destinations", params={"q": "empty"})
            bad_page = client.get("/api/v1/search/destinations", params={"page": 0})
            bad_rating = client.get("/api/v1/search/destinations", params={"minimum_rating": 5, "maximum_rating": 4})
            bad_sort = client.get("/api/v1/search/destinations", params={"sort_by": "unsafe"})
            failed = client.get("/api/v1/search/destinations", params={"q": "database-error"})
    finally: app.dependency_overrides.clear()
    assert empty.status_code == 200 and empty.json()["items"] == [] and empty.json()["total"] == 0
    assert bad_page.status_code == 422 and bad_rating.status_code == 422 and bad_sort.status_code == 422
    assert failed.status_code == 500 and failed.json() == {"detail": "Destination search could not complete the request"}


def test_public_contract_contains_no_review_or_administrative_data() -> None:
    service = FakeSearchService(); app.dependency_overrides[get_search_service] = lambda: service
    try:
        with TestClient(app) as client: response = client.get("/api/v1/search/destinations", params={"is_featured": True, "minimum_rating": 4})
    finally: app.dependency_overrides.clear()
    item = response.json()["items"][0]
    assert set(item) == {"id", "slug", "name_ar", "name_en", "short_description_ar", "short_description_en", "municipality", "region", "category", "primary_media_url", "is_featured", "average_rating", "reviews_count"}
    assert "reviews" not in item and "status" not in item
