import uuid

import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_db_session, require_permission
from app.main import app
from app.models import (
    Organization,
    OrganizationMembership,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.services.auth import create_user_access_token


@pytest.fixture
def override_db_session(app_instance: FastAPI, db_session):
    async def _override_db_session():
        yield db_session

    app_instance.dependency_overrides[get_db_session] = _override_db_session

    yield

    app_instance.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def app_instance():
    return app


@pytest.fixture
def rbac_test_router():
    router = APIRouter()

    @router.get("/test-rbac/orders")
    async def test_rbac_orders(
        _membership=Depends(require_permission("orders.create")),
    ):
        return {"allowed": True}

    return router


@pytest.mark.asyncio
async def test_rbac_allows_user_with_permission(
    db_session,
    override_db_session,
    app_instance,
    rbac_test_router,
):
    app_instance.include_router(rbac_test_router)

    organization = Organization(
        name="RBAC Allowed Organization",
        slug=f"rbac-allowed-{uuid.uuid4().hex[:8]}",
    )

    user = User(
        email=f"rbac-allowed-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="RBAC Allowed User",
    )

    role = Role(
        name="Cashier",
        code=f"rbac-cashier-{uuid.uuid4().hex[:8]}",
        is_system=False,
    )

    db_session.add_all([
        organization,
        user,
        role,
    ])

    await db_session.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=organization.id,
        role_id=role.id,
        is_active=True,
    )

    db_session.add(membership)

    permission = await db_session.scalar(
        select(Permission).where(
            Permission.code == "orders.create",
            Permission.is_active.is_(True),
        )
    )

    assert permission is not None

    role_permission = RolePermission(
        role_id=role.id,
        permission_id=permission.id,
    )

    db_session.add(role_permission)
    await db_session.commit()

    access_token = create_user_access_token(user)

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/test-rbac/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-ID": str(organization.id),
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "allowed": True,
    }

    await db_session.delete(role_permission)
    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)

    await db_session.commit()