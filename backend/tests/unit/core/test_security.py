from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import InvalidTokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verification() -> None:
    hashed = hash_password("CorrectHorseBatteryStaple!")
    assert hashed != "CorrectHorseBatteryStaple!"
    assert verify_password("CorrectHorseBatteryStaple!", hashed)
    assert not verify_password("wrong-password", hashed)
    assert not verify_password("password", "not-a-valid-password-hash")


def test_create_and_decode_access_token() -> None:
    token = create_access_token(42)
    assert decode_access_token(token).subject == 42


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        jwt.encode(
            {"sub": "1"},
            "wrong-signature-secret-that-is-long-enough",
            algorithm="HS256",
        ),
        jwt.encode(
            {"exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": "not-an-integer", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": "1", "exp": 4102444800},
            key="",
            algorithm="none",
        ),
        jwt.encode(
            {"sub": "", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": "0", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": "-1", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": "1.5", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
        jwt.encode(
            {"sub": True, "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        ),
    ],
)
def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_expired_token_is_rejected() -> None:
    token = create_access_token(1, expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
