from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import ReviewServiceDependency, require_content_admin
from app.api.pagination import LimitParameter, SkipParameter
from app.core.exceptions import (
    DestinationNotFoundError,
    ReviewError,
    ReviewIntegrityError,
    ReviewNotFoundError,
    ReviewPersistenceError,
    ReviewRatingError,
)
from app.models.review import Review, ReviewStatus
from app.schemas.review import (
    ReviewCreate,
    ReviewListResponse,
    ReviewModerationUpdate,
    ReviewRead,
    ReviewSortField,
    ReviewSortOrder,
    ReviewUpdate,
)


router = APIRouter(prefix="/reviews", tags=["Reviews"])


def raise_http_error(error: Exception) -> NoReturn:
    if isinstance(error, (ReviewNotFoundError, DestinationNotFoundError)):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, ReviewIntegrityError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, ReviewRatingError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, ReviewPersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Review service could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Review request failed") from error


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, service: ReviewServiceDependency) -> Review:
    try:
        return service.create_review(payload)
    except (ReviewError, DestinationNotFoundError) as error:
        raise_http_error(error)


@router.get("/destinations/{destination_id}", response_model=ReviewListResponse)
def list_approved_reviews(
    destination_id: int,
    service: ReviewServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
) -> ReviewListResponse:
    try:
        items, total = service.list_approved_by_destination(
            destination_id,
            skip=skip,
            limit=limit,
        )
    except ReviewError as error:
        raise_http_error(error)
    return ReviewListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.get("/admin", response_model=ReviewListResponse, tags=["Reviews Admin"], dependencies=[Depends(require_content_admin)])
def list_reviews_admin(
    service: ReviewServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
    destination_id: int | None = None,
    status_filter: Annotated[ReviewStatus | None, Query(alias="status")] = None,
    rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    is_verified: bool | None = None,
    sort_by: ReviewSortField = "created_at",
    sort_order: ReviewSortOrder = "desc",
) -> ReviewListResponse:
    try:
        items, total = service.list_reviews(
            skip=skip,
            limit=limit,
            destination_id=destination_id,
            status=status_filter,
            rating=rating,
            is_verified=is_verified,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ReviewError as error:
        raise_http_error(error)
    return ReviewListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.put("/admin/{review_id}", response_model=ReviewRead, tags=["Reviews Admin"], dependencies=[Depends(require_content_admin)])
def update_review_admin(
    review_id: int,
    payload: ReviewUpdate,
    service: ReviewServiceDependency,
) -> Review:
    try:
        return service.update_review(review_id, payload)
    except ReviewError as error:
        raise_http_error(error)


@router.patch(
    "/admin/{review_id}/status",
    response_model=ReviewRead,
    tags=["Reviews Admin"],
    dependencies=[Depends(require_content_admin)],
)
def moderate_review_admin(
    review_id: int,
    payload: ReviewModerationUpdate,
    service: ReviewServiceDependency,
) -> Review:
    try:
        return service.moderate_review(review_id, payload.status)
    except ReviewError as error:
        raise_http_error(error)


@router.delete(
    "/admin/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Reviews Admin"],
    dependencies=[Depends(require_content_admin)],
)
def delete_review_admin(review_id: int, service: ReviewServiceDependency) -> None:
    try:
        service.delete_review(review_id)
    except ReviewError as error:
        raise_http_error(error)


@router.get("/{review_id}", response_model=ReviewRead)
def get_approved_review(review_id: int, service: ReviewServiceDependency) -> Review:
    try:
        return service.get_approved_review(review_id)
    except ReviewError as error:
        raise_http_error(error)
