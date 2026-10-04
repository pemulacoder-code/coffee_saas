from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router
from app.db.session import get_db_session
from app.models.user import User
from app.api.dependencies import get_current_user


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_login_success() -> None:
    app = create_test_app()

    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "user@example.com"
    user.password_hash = "hashed-password"
    user.is_active = True

    mock_session = AsyncMock()

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    with (
        patch(
            "app.api.auth.authenticate_user",
            new_callable=AsyncMock,
            return_value=user,
        ),
        patch(
            "app.api.auth.create_user_access_token",
            return_value="test-access-token",
        ),
    ):
        client = TestClient(app)

        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "test-access-token",
        "token_type": "bearer",
    }


def test_login_invalid_credentials() -> None:
    app = create_test_app()

    mock_session = AsyncMock()

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    with patch(
        "app.api.auth.authenticate_user",
        new_callable=AsyncMock,
        return_value=None,
    ):
        client = TestClient(app)

        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_get_me() -> None:
    app = create_test_app()

    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "user@example.com"

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer test-access-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "email": "user@example.com",
    }

def test_get_me_without_token() -> None:
    app = create_test_app()

    client = TestClient(app)

    response = client.get("/auth/me")

    assert response.status_code == 401