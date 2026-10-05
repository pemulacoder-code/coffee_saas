import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_db_session
from app.main import app
from app.models import (
    Branch,
    Organization,
    OrganizationMembership,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.services.auth import create_user_access_token


@pytest.fixture
def override_db_session(app_instance, db_session):
    async def _override_db_session():
        yield db_session

    app_instance.dependency_overrides[get_db_session] = _override_db_session

    yield

    app_instance.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def app_instance():
    return app


async def create_branch_test_context(
    db_session,
    *,
    role_code: str,
    permission_codes: list[str],
):
    organization = Organization(
        name=f"Branch Test Organization {uuid.uuid4().hex[:8]}",
        slug=f"branch-test-{uuid.uuid4().hex[:8]}",
    )

    user = User(
        email=f"branch-test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="Branch Test User",
    )

    role = Role(
        name=f"Branch Test Role {uuid.uuid4().hex[:8]}",
        code=role_code,
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

    permissions = []

    for permission_code in permission_codes:
        permission = await db_session.scalar(
            select(Permission).where(
                Permission.code == permission_code,
                Permission.is_active.is_(True),
            )
        )

        assert permission is not None

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )

        db_session.add(role_permission)
        permissions.append(role_permission)

    await db_session.commit()

    return organization, user, role, membership, permissions


def auth_headers(user, organization):
    access_token = create_user_access_token(user)

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": str(organization.id),
    }


@pytest.mark.asyncio
async def test_list_branches_requires_permission(
    db_session,
    override_db_session,
    app_instance,
):
    organization, user, role, membership, permissions = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-read-{uuid.uuid4().hex[:8]}",
            permission_codes=[],
        )
    )

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/branches",
            headers=auth_headers(user, organization),
        )

    assert response.status_code == 403

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_branch(
    db_session,
    override_db_session,
    app_instance,
):
    organization, user, role, membership, permissions = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-create-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.create"],
        )
    )

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/branches",
            headers=auth_headers(user, organization),
            json={
                "name": "Main Branch",
                "code": "MAIN",
                "address": "Main Street",
                "phone": "08123456789",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["organization_id"] == str(organization.id)
    assert data["name"] == "Main Branch"
    assert data["code"] == "MAIN"
    assert data["address"] == "Main Street"
    assert data["phone"] == "08123456789"
    assert data["is_active"] is True

    branch = await db_session.scalar(
        select(Branch).where(
            Branch.id == uuid.UUID(data["id"]),
        )
    )

    assert branch is not None
    assert branch.organization_id == organization.id

    await db_session.delete(branch)
    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_branches_is_tenant_isolated(
    db_session,
    override_db_session,
    app_instance,
):
    organization_a, user_a, role_a, membership_a, permissions_a = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-tenant-a-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.read"],
        )
    )

    organization_b = Organization(
        name=f"Other Organization {uuid.uuid4().hex[:8]}",
        slug=f"other-org-{uuid.uuid4().hex[:8]}",
    )

    db_session.add(organization_b)
    await db_session.flush()

    branch_a = Branch(
        organization_id=organization_a.id,
        name="Branch A",
        code="BR-A",
        is_active=True,
    )

    branch_b = Branch(
        organization_id=organization_b.id,
        name="Branch B",
        code="BR-B",
        is_active=True,
    )

    db_session.add_all([
        branch_a,
        branch_b,
    ])

    await db_session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/branches",
            headers=auth_headers(user_a, organization_a),
        )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert str(branch_a.id) in returned_ids
    assert str(branch_b.id) not in returned_ids

    await db_session.delete(branch_a)
    await db_session.delete(branch_b)
    await db_session.delete(membership_a)
    await db_session.delete(user_a)
    await db_session.delete(role_a)
    await db_session.delete(organization_a)
    await db_session.delete(organization_b)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_branch_from_other_tenant_returns_404(
    db_session,
    override_db_session,
    app_instance,
):
    organization_a, user_a, role_a, membership_a, permissions_a = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-isolation-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.read"],
        )
    )

    organization_b = Organization(
        name=f"Other Organization {uuid.uuid4().hex[:8]}",
        slug=f"other-org-{uuid.uuid4().hex[:8]}",
    )

    db_session.add(organization_b)
    await db_session.flush()

    branch_b = Branch(
        organization_id=organization_b.id,
        name="Private Branch B",
        code="PRIVATE-B",
        is_active=True,
    )

    db_session.add(branch_b)
    await db_session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/branches/{branch_b.id}",
            headers=auth_headers(user_a, organization_a),
        )

    assert response.status_code == 404

    await db_session.delete(branch_b)
    await db_session.delete(membership_a)
    await db_session.delete(user_a)
    await db_session.delete(role_a)
    await db_session.delete(organization_a)
    await db_session.delete(organization_b)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_branch(
    db_session,
    override_db_session,
    app_instance,
):
    organization, user, role, membership, permissions = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-update-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.update"],
        )
    )

    branch = Branch(
        organization_id=organization.id,
        name="Old Name",
        code="OLD",
        is_active=True,
    )

    db_session.add(branch)
    await db_session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/branches/{branch.id}",
            headers=auth_headers(user, organization),
            json={
                "name": "New Name",
                "code": "NEW",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Name"
    assert data["code"] == "NEW"

    await db_session.refresh(branch)

    assert branch.name == "New Name"
    assert branch.code == "NEW"

    await db_session.delete(branch)
    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)
    await db_session.commit()


@pytest.mark.asyncio
async def test_delete_branch_soft_deletes(
    db_session,
    override_db_session,
    app_instance,
):
    organization, user, role, membership, permissions = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-delete-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.delete"],
        )
    )

    branch = Branch(
        organization_id=organization.id,
        name="Delete Me",
        code="DELETE-ME",
        is_active=True,
    )

    db_session.add(branch)
    await db_session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.delete(
            f"/branches/{branch.id}",
            headers=auth_headers(user, organization),
        )

    assert response.status_code == 200

    data = response.json()

    assert data["is_active"] is False

    await db_session.refresh(branch)

    assert branch.is_active is False

    await db_session.delete(branch)
    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)
    await db_session.commit()


@pytest.mark.asyncio
async def test_duplicate_branch_code_returns_conflict(
    db_session,
    override_db_session,
    app_instance,
):
    organization, user, role, membership, permissions = (
        await create_branch_test_context(
            db_session,
            role_code=f"branch-duplicate-{uuid.uuid4().hex[:8]}",
            permission_codes=["branches.create"],
        )
    )

    existing_branch = Branch(
        organization_id=organization.id,
        name="Existing Branch",
        code="DUPLICATE",
        is_active=True,
    )

    db_session.add(existing_branch)
    await db_session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/branches",
            headers=auth_headers(user, organization),
            json={
                "name": "Another Branch",
                "code": "DUPLICATE",
            },
        )

    assert response.status_code == 409

    await db_session.rollback()

    await db_session.delete(existing_branch)
    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)
    await db_session.commit()