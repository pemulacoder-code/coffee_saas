from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.security import hash_password
from app.services.auth import (
    authenticate_user,
    create_user_access_token,
    get_user_by_email,
)


def make_user(
    *,
    email: str = "user@example.com",
    password: str = "StrongPassword123!",
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock()

    user.id = "12345678-1234-5678-1234-567812345678"
    user.email = email
    user.password_hash = hash_password(password)
    user.is_active = is_active
    user.full_name = "Test User"

    return user


@pytest.mark.asyncio
async def test_get_user_by_email_returns_user() -> None:
    session = AsyncMock()
    user = make_user()

    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    session.execute.return_value = result

    found_user = await get_user_by_email(
        session=session,
        email="user@example.com",
    )

    assert found_user is user
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_email_returns_none_when_not_found() -> None:
    session = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    session.execute.return_value = result

    found_user = await get_user_by_email(
        session=session,
        email="missing@example.com",
    )

    assert found_user is None
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_authenticate_user_success() -> None:
    session = AsyncMock()
    user = make_user()

    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    session.execute.return_value = result

    authenticated_user = await authenticate_user(
        session=session,
        email="user@example.com",
        password="StrongPassword123!",
    )

    assert authenticated_user is user


@pytest.mark.asyncio
async def test_authenticate_user_rejects_wrong_password() -> None:
    session = AsyncMock()
    user = make_user()

    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    session.execute.return_value = result

    authenticated_user = await authenticate_user(
        session=session,
        email="user@example.com",
        password="WrongPassword123!",
    )

    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_rejects_unknown_user() -> None:
    session = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    session.execute.return_value = result

    authenticated_user = await authenticate_user(
        session=session,
        email="missing@example.com",
        password="StrongPassword123!",
    )

    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_rejects_inactive_user() -> None:
    session = AsyncMock()
    user = make_user(is_active=False)

    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    session.execute.return_value = result

    authenticated_user = await authenticate_user(
        session=session,
        email="user@example.com",
        password="StrongPassword123!",
    )

    assert authenticated_user is None


def test_create_user_access_token() -> None:
    user = make_user()

    token = create_user_access_token(user)

    assert isinstance(token, str)
    assert token
