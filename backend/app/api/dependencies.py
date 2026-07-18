from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.destination import DestinationService


DatabaseSession = Annotated[Session, Depends(get_db)]


def get_destination_service(db: DatabaseSession) -> DestinationService:
    return DestinationService(db)


DestinationServiceDependency = Annotated[
    DestinationService,
    Depends(get_destination_service),
]
