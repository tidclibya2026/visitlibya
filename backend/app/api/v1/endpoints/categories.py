from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CategoryServiceDependency, require_content_admin
from app.api.pagination import LimitParameter, SkipParameter
from app.core.exceptions import (
    CategoryCodeConflictError,
    CategoryError,
    CategoryIntegrityError,
    CategoryNotFoundError,
    CategoryPersistenceError,
)
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryRead,
    CategoryUpdate,
)


router = APIRouter(prefix="/categories", tags=["Categories"])


def raise_http_error(error: CategoryError) -> NoReturn:
    if isinstance(error, CategoryNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, CategoryCodeConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, CategoryIntegrityError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, CategoryPersistenceError):
        raise HTTPException(
            status_code=500,
            detail="Category service could not complete the request",
        ) from error
    raise HTTPException(status_code=500, detail="Category request failed") from error


@router.get("", response_model=CategoryListResponse)
def list_categories(
    service: CategoryServiceDependency,
    skip: SkipParameter = 0,
    limit: LimitParameter = 20,
    is_active: bool | None = True,
) -> CategoryListResponse:
    try:
        items, total = service.list_categories(
            skip=skip,
            limit=limit,
            is_active=is_active,
        )
    except CategoryError as error:
        raise_http_error(error)
    return CategoryListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_content_admin)])
def create_category(
    payload: CategoryCreate,
    service: CategoryServiceDependency,
) -> Category:
    try:
        return service.create_category(payload)
    except CategoryError as error:
        raise_http_error(error)


@router.get("/{code}", response_model=CategoryRead)
def get_category(code: str, service: CategoryServiceDependency) -> Category:
    try:
        return service.get_category_by_code(code)
    except CategoryError as error:
        raise_http_error(error)


@router.put("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_content_admin)])
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: CategoryServiceDependency,
) -> Category:
    try:
        return service.update_category(category_id, payload)
    except CategoryError as error:
        raise_http_error(error)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_content_admin)])
def delete_category(
    category_id: int,
    service: CategoryServiceDependency,
) -> None:
    try:
        service.delete_category(category_id)
    except CategoryError as error:
        raise_http_error(error)
