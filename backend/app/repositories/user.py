from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def create(self, user: User) -> User:
        self.add(user)
        self.flush()
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email)
        )

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )

    def get_by_login_identifier(self, identifier: str) -> User | None:
        """Use an exact indexed lookup: email when `@` is present, otherwise username."""
        if "@" in identifier:
            return self.get_by_email(identifier)
        return self.get_by_username(identifier)
