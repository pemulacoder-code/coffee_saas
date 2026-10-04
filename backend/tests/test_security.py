from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext() -> None:
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2")


def test_password_verification_success() -> None:
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_password_verification_failure() -> None:
    password = "StrongPassword123!"
    wrong_password = "WrongPassword123!"

    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_create_and_decode_access_token() -> None:
    user_id = "user-123"

    token = create_access_token(subject=user_id)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload


def test_access_token_with_additional_claims() -> None:
    token = create_access_token(
        subject="user-123",
        additional_claims={
            "role": "admin",
            "organization_id": "org-123",
        },
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"
    assert payload["organization_id"] == "org-123"


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("this-is-not-a-valid-jwt")


def test_non_access_token_is_rejected() -> None:
    payload = {
        "sub": "user-123",
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_expired_token_is_rejected() -> None:
    token = create_access_token(
        subject="user-123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
