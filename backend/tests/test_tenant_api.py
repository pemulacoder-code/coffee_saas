import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_db_session
from app.main import app
from app.models import Organization, OrganizationMembership, Role, User
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


@pytest.mark.asyncio
async def test_get_tenant_returns_current_organization(
    db_session,
    override_db_session,
):
    organization = Organization(
        name="Tenant API Test",
        slug=f"tenant-api-{uuid.uuid4().hex[:8]}",
    )

    user = User(
        email=f"tenant-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="Tenant API User",
    )

    role = Role(
        name="Owner",
        code=f"owner-tenant-api-{uuid.uuid4().hex[:8]}",
        is_system=True,
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
    await db_session.commit()

    access_token = create_user_access_token(user)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-ID": str(organization.id),
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "organization_id": str(organization.id),
    }

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)

    await db_session.commit()


@pytest.mark.asyncio
async def test_tenant_isolation_between_organizations(
    db_session,
    override_db_session,
):
    organization_a = Organization(
        name="Organization A",
        slug=f"organization-a-{uuid.uuid4().hex[:8]}",
    )

    organization_b = Organization(
        name="Organization B",
        slug=f"organization-b-{uuid.uuid4().hex[:8]}",
    )

    user_a = User(
        email=f"user-a-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="User A",
    )

    user_b = User(
        email=f"user-b-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="User B",
    )

    role = Role(
        name="Owner",
        code=f"owner-isolation-{uuid.uuid4().hex[:8]}",
        is_system=True,
    )

    db_session.add_all([
        organization_a,
        organization_b,
        user_a,
        user_b,
        role,
    ])

    await db_session.flush()

    membership_a = OrganizationMembership(
        user_id=user_a.id,
        organization_id=organization_a.id,
        role_id=role.id,
        is_active=True,
    )

    membership_b = OrganizationMembership(
        user_id=user_b.id,
        organization_id=organization_b.id,
        role_id=role.id,
        is_active=True,
    )

    db_session.add_all([
        membership_a,
        membership_b,
    ])

    await db_session.commit()

    token_a = create_user_access_token(user_a)
    token_b = create_user_access_token(user_b)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response_a_to_a = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Organization-ID": str(organization_a.id),
            },
        )

        response_a_to_b = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Organization-ID": str(organization_b.id),
            },
        )

        response_b_to_b = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {token_b}",
                "X-Organization-ID": str(organization_b.id),
            },
        )

    assert response_a_to_a.status_code == 200
    assert response_a_to_a.json() == {
        "organization_id": str(organization_a.id),
    }

    assert response_a_to_b.status_code == 403
    assert response_a_to_b.json() == {
        "detail": "User is not a member of this organization",
    }

    assert response_b_to_b.status_code == 200
    assert response_b_to_b.json() == {
        "organization_id": str(organization_b.id),
    }

    await db_session.delete(membership_a)
    await db_session.delete(membership_b)
    await db_session.delete(user_a)
    await db_session.delete(user_b)
    await db_session.delete(role)
    await db_session.delete(organization_a)
    await db_session.delete(organization_b)

    await db_session.commit()

@pytest.mark.asyncio
async def test_tenant_rejects_inactive_membership(
    db_session,
    override_db_session,
):
    organization = Organization(
        name="Inactive Membership Org",
        slug=f"inactive-membership-{uuid.uuid4().hex[:8]}",
    )

    user = User(
        email=f"inactive-membership-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="Inactive Membership User",
    )

    role = Role(
        name="Owner",
        code=f"owner-inactive-membership-{uuid.uuid4().hex[:8]}",
        is_system=True,
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
        is_active=False,
    )

    db_session.add(membership)
    await db_session.commit()

    token = create_user_access_token(user)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": str(organization.id),
            },
        )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "User is not a member of this organization",
    }

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)

    await db_session.commit()


@pytest.mark.asyncio
async def test_tenant_rejects_inactive_organization(
    db_session,
    override_db_session,
):
    organization = Organization(
        name="Inactive Organization",
        slug=f"inactive-organization-{uuid.uuid4().hex[:8]}",
        is_active=False,
    )

    user = User(
        email=f"inactive-org-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="Inactive Organization User",
    )

    role = Role(
        name="Owner",
        code=f"owner-inactive-org-{uuid.uuid4().hex[:8]}",
        is_system=True,
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
    await db_session.commit()

    token = create_user_access_token(user)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/tenant",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": str(organization.id),
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization not found",
    }

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)

    await db_session.commit()