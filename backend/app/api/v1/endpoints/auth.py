from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import AuthServiceDependency, CurrentActiveUserDependency
from app.core.exceptions import (
    AuthenticationError,
    AuthenticationPersistenceError,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, TokenResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


def raise_http_error(error: AuthenticationError) -> NoReturn:
    if isinstance(error, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    if isinstance(error, InactiveUserError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, AuthenticationPersistenceError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is unavailable",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Authentication request failed",
    ) from error


@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDependency,
) -> TokenResponse:
    try:
        return service.login(form.username, form.password)
    except AuthenticationError as error:
        raise_http_error(error)


@router.get("/me", response_model=CurrentUserResponse)
def current_user(user: CurrentActiveUserDependency) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=[role.name for role in user.roles],
    )
