from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.category import CategoryService
from app.services.destination import DestinationService
from app.services.media import MediaService
from app.services.review import ReviewService
from app.services.search import SearchService


DatabaseSession = Annotated[Session, Depends(get_db)]


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
