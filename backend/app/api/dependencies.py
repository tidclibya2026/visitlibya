from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.exceptions import (
    AuthenticationPersistenceError,
    InactiveUserError,
    InvalidTokenError,
)
from app.core.security import decode_access_token, oauth2_scheme
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.destination import DestinationService
from app.services.media import MediaService
from app.services.review import ReviewService
from app.services.search import SearchService


DatabaseSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DatabaseSession) -> UserRepository:
    return UserRepository(db)


UserRepositoryDependency = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(
    db: DatabaseSession,
    repository: UserRepositoryDependency,
) -> AuthService:
    return AuthService(db, repository)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: AuthServiceDependency,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        return service.get_user_by_id(payload.subject)
    except InvalidTokenError as exc:
        raise credentials_error from exc
    except AuthenticationPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is unavailable",
        ) from exc


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


def get_current_active_user(user: CurrentUserDependency) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(InactiveUserError()),
        )
    return user


CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]


def get_category_service(db: DatabaseSession) -> CategoryService:
    return CategoryService(db)


CategoryServiceDependency = Annotated[
    CategoryService,
    Depends(get_category_service),
]


def get_destination_service(db: DatabaseSession) -> DestinationService:
    return DestinationService(db)


DestinationServiceDependency = Annotated[
    DestinationService,
    Depends(get_destination_service),
]


def get_media_service(db: DatabaseSession) -> MediaService:
    return MediaService(db)


MediaServiceDependency = Annotated[MediaService, Depends(get_media_service)]


def get_review_service(db: DatabaseSession) -> ReviewService:
    return ReviewService(db)


ReviewServiceDependency = Annotated[ReviewService, Depends(get_review_service)]


def get_search_service(db: DatabaseSession) -> SearchService:
    return SearchService(db)


SearchServiceDependency = Annotated[SearchService, Depends(get_search_service)]
