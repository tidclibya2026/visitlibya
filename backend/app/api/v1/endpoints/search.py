from typing import Annotated, NoReturn

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import SearchServiceDependency
from app.core.exceptions import SearchError, SearchPersistenceError, SearchValidationError
from app.schemas.search import (
    SearchDestinationResponse,
    SearchFilters,
    SearchSortField,
    SearchSortOrder,
)


router = APIRouter(prefix="/search", tags=["Search"])


def raise_http_error(error: SearchError) -> NoReturn:
    if isinstance(error, SearchValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, SearchPersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Destination search could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Search request failed") from error


@router.get("/destinations", response_model=SearchDestinationResponse)
def search_destinations(
    service: SearchServiceDependency,
    q: Annotated[str | None, Query(max_length=250)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    city: Annotated[str | None, Query(max_length=150)] = None,
    region: Annotated[str | None, Query(max_length=150)] = None,
    is_featured: bool | None = None,
    minimum_rating: Annotated[float | None, Query(ge=1, le=5)] = None,
    maximum_rating: Annotated[float | None, Query(ge=1, le=5)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: SearchSortField = "name",
    sort_order: SearchSortOrder = "asc",
) -> SearchDestinationResponse:
    try:
        if (
            minimum_rating is not None
            and maximum_rating is not None
            and minimum_rating > maximum_rating
        ):
            raise SearchValidationError(
                "minimum_rating cannot exceed maximum_rating"
            )
        filters = SearchFilters.model_construct(
            q=q,
            category_id=category_id,
            city=city,
            region=region,
            is_featured=is_featured,
            minimum_rating=minimum_rating,
            maximum_rating=maximum_rating,
        )
        return service.search_destinations(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except SearchError as error:
        raise_http_error(error)
