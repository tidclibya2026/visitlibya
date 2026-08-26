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
from app.repositories.favorite import FavoriteRepository
from app.repositories.destination_planner_profile import (
    DestinationPlannerProfileRepository,
)
from app.repositories.trip import TripRepository
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.destination import DestinationService
from app.services.destination_planner_profile import (
    DestinationPlannerProfileService,
)
from app.services.media import MediaService
from app.services.review import ReviewService
from app.services.search import SearchService
from app.services.favorite import FavoriteService
from app.services.trip import TripService


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

CONTENT_ADMIN_ROLE_CODES = frozenset({"content_admin"})


def require_content_admin(user: CurrentActiveUserDependency) -> User:
    authorized = user.is_superuser or any(
        role.is_active and role.code in CONTENT_ADMIN_ROLE_CODES for role in user.roles
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


ContentAdminDependency = Annotated[User, Depends(require_content_admin)]


def get_favorite_repository(db: DatabaseSession) -> FavoriteRepository:
    return FavoriteRepository(db)


FavoriteRepositoryDependency = Annotated[
    FavoriteRepository,
    Depends(get_favorite_repository),
]


def get_favorite_service(
    db: DatabaseSession,
    repository: FavoriteRepositoryDependency,
) -> FavoriteService:
    return FavoriteService(db, repository)


FavoriteServiceDependency = Annotated[
    FavoriteService,
    Depends(get_favorite_service),
]


def get_trip_repository(db: DatabaseSession) -> TripRepository:
    return TripRepository(db)


TripRepositoryDependency = Annotated[TripRepository, Depends(get_trip_repository)]


def get_trip_service(
    db: DatabaseSession,
    repository: TripRepositoryDependency,
) -> TripService:
    return TripService(db, repository)


TripServiceDependency = Annotated[TripService, Depends(get_trip_service)]


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


def get_destination_planner_profile_repository(
    db: DatabaseSession,
) -> DestinationPlannerProfileRepository:
    return DestinationPlannerProfileRepository(db)


DestinationPlannerProfileRepositoryDependency = Annotated[
    DestinationPlannerProfileRepository,
    Depends(get_destination_planner_profile_repository),
]


def get_destination_planner_profile_service(
    db: DatabaseSession,
    repository: DestinationPlannerProfileRepositoryDependency,
) -> DestinationPlannerProfileService:
    return DestinationPlannerProfileService(db, repository)


DestinationPlannerProfileServiceDependency = Annotated[
    DestinationPlannerProfileService,
    Depends(get_destination_planner_profile_service),
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
