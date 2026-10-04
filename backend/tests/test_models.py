import uuid

import pytest
from sqlalchemy import select

from app.models import (
    Organization,
    OrganizationMembership,
    Role,
    User,
)


@pytest.mark.asyncio
async def test_create_organization(db_session):
    organization = Organization(
        name="Test Coffee",
        slug=f"test-coffee-{uuid.uuid4().hex[:8]}",
    )

    db_session.add(organization)
    await db_session.commit()
    await db_session.refresh(organization)

    assert organization.id is not None
    assert organization.name == "Test Coffee"

    await db_session.delete(organization)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_identity_and_membership(db_session):
    organization = Organization(
        name="Membership Test",
        slug=f"membership-test-{uuid.uuid4().hex[:8]}",
    )

    user = User(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        full_name="Test User",
    )

    role = Role(
        name="Owner",
        code=f"owner-test-{uuid.uuid4().hex[:8]}",
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
    )

    db_session.add(membership)
    await db_session.commit()

    result = await db_session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.id == membership.id
        )
    )

    saved_membership = result.scalar_one()

    assert saved_membership.user_id == user.id
    assert saved_membership.organization_id == organization.id
    assert saved_membership.role_id == role.id

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.delete(role)
    await db_session.delete(organization)

    await db_session.commit()