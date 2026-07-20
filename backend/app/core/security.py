from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError as PyJWTInvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings
from app.core.exceptions import InvalidTokenError
from app.schemas.auth import TokenPayload


ALLOWED_JWT_ALGORITHMS = ("HS256",)
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except (TypeError, UnknownHashError, ValueError):
        return False


def create_access_token(
    subject: int | str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {"sub": str(subject), "iat": now, "exp": expires_at},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=list(ALLOWED_JWT_ALGORITHMS),
            options={"require": ["exp", "sub"]},
        )
        raw_subject = payload.get("sub")
        subject = int(raw_subject)
        if subject <= 0:
            raise ValueError
    except (PyJWTInvalidTokenError, TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc
    return TokenPayload(subject=subject)
