from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.dependencies import require_permission
from app.core.tenant import TenantContext


@pytest.mark.asyncio
async def test_require_permission_allows_user_with_permission() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    membership = MagicMock()
    membership.is_active = True

    role = MagicMock()
    role.is_active = True

    permission = MagicMock()
    permission.code = "orders.create"
    permission.is_active = True

    session = AsyncMock()
    session.scalar.side_effect = [
        membership,
        role,
        permission,
    ]

    dependency = require_permission("orders.create")

    result = await dependency(
        tenant=TenantContext(organization_id=organization_id),
        current_user=current_user,
        session=session,
    )

    assert result == membership


@pytest.mark.asyncio
async def test_require_permission_rejects_missing_permission() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    membership = MagicMock()
    membership.is_active = True

    role = MagicMock()
    role.is_active = True

    session = AsyncMock()
    session.scalar.side_effect = [
        membership,
        role,
        None,
    ]

    dependency = require_permission("orders.create")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            tenant=TenantContext(organization_id=organization_id),
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Permission denied"


@pytest.mark.asyncio
async def test_require_permission_rejects_missing_membership() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    session = AsyncMock()
    session.scalar.return_value = None

    dependency = require_permission("orders.create")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            tenant=TenantContext(organization_id=organization_id),
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "User is not a member of this organization"
    )


@pytest.mark.asyncio
async def test_require_permission_rejects_inactive_membership() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    session = AsyncMock()
    session.scalar.return_value = None

    dependency = require_permission("orders.create")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            tenant=TenantContext(organization_id=organization_id),
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "User is not a member of this organization"
    )


@pytest.mark.asyncio
async def test_require_permission_rejects_inactive_role() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    membership = MagicMock()
    membership.is_active = True

    session = AsyncMock()
    session.scalar.side_effect = [
        membership,
        None,
    ]

    dependency = require_permission("orders.create")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            tenant=TenantContext(organization_id=organization_id),
            current_user=current_user,
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Permission denied"


@pytest.mark.asyncio
async def test_require_permission_uses_current_tenant_membership() -> None:
    user_id = uuid4()
    organization_a_id = uuid4()
    organization_b_id = uuid4()

    current_user = MagicMock()
    current_user.id = user_id

    membership = MagicMock()
    membership.is_active = True

    role = MagicMock()
    role.is_active = True

    permission = MagicMock()
    permission.code = "orders.create"
    permission.is_active = True

    session = AsyncMock()
    session.scalar.side_effect = [
        membership,
        role,
        permission,
    ]

    dependency = require_permission("orders.create")

    result = await dependency(
        tenant=TenantContext(organization_id=organization_a_id),
        current_user=current_user,
        session=session,
    )

    assert result == membership

    membership_query = session.scalar.await_args_list[0].args[0]
    query_sql = str(membership_query)

    assert "organization_memberships" in query_sql
