from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.dependencies import get_current_tenant
from app.core.tenant import TenantContext


@pytest.mark.asyncio
async def test_get_current_tenant_returns_context_for_active_member() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    organization = MagicMock()
    organization.is_active = True

    membership = MagicMock()
    membership.is_active = True

    session = AsyncMock()
    session.get.return_value = organization
    session.scalar.return_value = membership

    result = await get_current_tenant(
        organization_id=organization_id,
        current_user=current_user,
        session=session,
    )

    assert isinstance(result, TenantContext)
    assert result.organization_id == organization_id

    session.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_tenant_rejects_unknown_organization() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(
            organization_id=organization_id,
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Organization not found"

    session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_tenant_rejects_inactive_organization() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    organization = MagicMock()
    organization.is_active = False

    session = AsyncMock()
    session.get.return_value = organization

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(
            organization_id=organization_id,
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Organization not found"

    session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_tenant_rejects_non_member() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    organization = MagicMock()
    organization.is_active = True

    session = AsyncMock()
    session.get.return_value = organization
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(
            organization_id=organization_id,
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "User is not a member of this organization"
    )


@pytest.mark.asyncio
async def test_get_current_tenant_rejects_inactive_membership() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    organization = MagicMock()
    organization.is_active = True

    session = AsyncMock()
    session.get.return_value = organization
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(
            organization_id=organization_id,
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "User is not a member of this organization"
    )