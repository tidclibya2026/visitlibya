from typing import Generic, TypeVar

from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Small shared unit-of-work helpers; transaction ownership stays in services."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entity: ModelT) -> None:
        self.session.add(entity)

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)

    def flush(self) -> None:
        self.session.flush()

    def refresh(self, entity: ModelT) -> None:
        self.session.refresh(entity)
