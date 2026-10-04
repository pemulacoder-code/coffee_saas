from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


@pytest.mark.asyncio
async def test_get_current_user_returns_user() -> None:
    user_id = uuid4()

    token = create_access_token(
        subject=str(user_id),
    )

    user = MagicMock()
    user.id = user_id
    user.is_active = True

    session = AsyncMock()
    session.get.return_value = user

    credentials = make_credentials(token)

    result = await get_current_user(
        credentials=credentials,
        session=session,
    )

    assert result is user
    session.get.assert_awaited_once_with(
        User,
        user_id,
    )


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    session = AsyncMock()

    credentials = make_credentials(
        "not-a-valid-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exc_info.value.status_code == 401
    assert (
        exc_info.value.detail
        == "Invalid authentication credentials"
    )


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_subject() -> None:
    token = jwt.encode(
        {
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    session = AsyncMock()
    credentials = make_credentials(token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_uuid() -> None:
    token = create_access_token(
        subject="not-a-uuid",
    )

    session = AsyncMock()
    credentials = make_credentials(token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_unknown_user() -> None:
    user_id = uuid4()

    token = create_access_token(
        subject=str(user_id),
    )

    session = AsyncMock()
    session.get.return_value = None

    credentials = make_credentials(token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_user() -> None:
    user_id = uuid4()

    token = create_access_token(
        subject=str(user_id),
    )

    user = MagicMock()
    user.id = user_id
    user.is_active = False

    session = AsyncMock()
    session.get.return_value = user

    credentials = make_credentials(token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User is inactive"
