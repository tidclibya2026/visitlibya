from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.category import CategoryService
from app.services.destination import DestinationService
from app.services.media import MediaService


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
