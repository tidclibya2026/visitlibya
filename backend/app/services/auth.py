from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationPersistenceError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RegistrationConflictError,
    UsernameAlreadyRegisteredError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse, UserRegistrationRequest


DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$ufWdF1r8dT81EvBrIDD3rA"
    "$GB3zLjRjsCtA/39JruBLeJrplrV5kZBJhNCXAQxkqio"
)


class AuthService:
    def __init__(self, session: Session, repository: UserRepository | None = None) -> None:
        self.session = session
        self.repository = repository or UserRepository(session)

    def login(self, identifier: str, password: str) -> TokenResponse:
        normalized_identifier = identifier.strip()
        try:
            user = self.repository.get_by_login_identifier(normalized_identifier)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise AuthenticationPersistenceError() from exc

        password_matches = verify_password(
            password,
            user.hashed_password if user is not None else DUMMY_PASSWORD_HASH,
        )
        if user is None or not password_matches:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()

        return TokenResponse(
            access_token=create_access_token(user.id),
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def register(self, payload: UserRegistrationRequest) -> User:
        try:
            if self.repository.get_by_email(str(payload.email)):
                raise EmailAlreadyRegisteredError()
            if self.repository.get_by_username(payload.username):
                raise UsernameAlreadyRegisteredError()

            user = User(
                full_name=payload.full_name,
                email=str(payload.email),
                username=payload.username,
                hashed_password=hash_password(payload.password),
                is_active=True,
                is_superuser=False,
                roles=[],
            )
            self.repository.create(user)
            self.session.commit()
            return user
        except RegistrationConflictError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise RegistrationConflictError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise AuthenticationPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def get_user_by_id(self, user_id: int) -> User:
        try:
            user = self.repository.get_by_id(user_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise AuthenticationPersistenceError() from exc
        if user is None:
            raise InvalidTokenError()
        return user

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
