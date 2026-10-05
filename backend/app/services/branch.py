from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchUpdate


class BranchService:
    @staticmethod
    async def list_branches(
        session: AsyncSession,
        tenant: TenantContext,
    ) -> list[Branch]:
        result = await session.scalars(
            select(Branch)
            .where(
                Branch.organization_id == tenant.organization_id,
            )
            .order_by(Branch.name.asc())
        )
        return list(result.all())

    @staticmethod
    async def get_branch(
        session: AsyncSession,
        tenant: TenantContext,
        branch_id: UUID,
    ) -> Branch | None:
        return await session.scalar(
            select(Branch).where(
                Branch.id == branch_id,
                Branch.organization_id == tenant.organization_id,
            )
        )

    @staticmethod
    async def create_branch(
        session: AsyncSession,
        tenant: TenantContext,
        data: BranchCreate,
    ) -> Branch:
        branch = Branch(
            organization_id=tenant.organization_id,
            name=data.name,
            code=data.code,
            address=data.address,
            phone=data.phone,
            is_active=True,
        )

        session.add(branch)

        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            raise

        await session.refresh(branch)

        return branch

    @staticmethod
    async def update_branch(
        session: AsyncSession,
        tenant: TenantContext,
        branch_id: UUID,
        data: BranchUpdate,
    ) -> Branch | None:
        branch = await BranchService.get_branch(
            session=session,
            tenant=tenant,
            branch_id=branch_id,
        )

        if branch is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(branch, field, value)

        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            raise

        await session.refresh(branch)

        return branch

    @staticmethod
    async def delete_branch(
        session: AsyncSession,
        tenant: TenantContext,
        branch_id: UUID,
    ) -> Branch | None:
        branch = await BranchService.get_branch(
            session=session,
            tenant=tenant,
            branch_id=branch_id,
        )

        if branch is None:
            return None

        branch.is_active = False

        await session.flush()
        await session.refresh(branch)

        return branch