from pydantic import ValidationError
import pytest

from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)


def test_login_request_accepts_valid_data() -> None:
    data = LoginRequest(
        email="user@example.com",
        password="StrongPassword123!",
    )

    assert data.email == "user@example.com"
    assert data.password == "StrongPassword123!"


def test_login_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="user@example.com",
            password="short",
        )


def test_login_request_rejects_short_email() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="a",
            password="StrongPassword123!",
        )


def test_token_response_defaults_to_bearer() -> None:
    response = TokenResponse(
        access_token="test-token",
    )

    assert response.access_token == "test-token"
    assert response.token_type == "bearer"


def test_refresh_token_request() -> None:
    request = RefreshTokenRequest(
        refresh_token="refresh-token",
    )

    assert request.refresh_token == "refresh-token"


def test_current_user_response() -> None:
    response = CurrentUserResponse(
        id="user-123",
        email="user@example.com",
    )

    assert response.id == "user-123"
    assert response.email == "user@example.com"


def test_current_user_response_does_not_expose_password() -> None:
    response = CurrentUserResponse(
        id="user-123",
        email="user@example.com",
    )

    assert "password" not in response.model_dump()
    assert "password_hash" not in response.model_dump()
