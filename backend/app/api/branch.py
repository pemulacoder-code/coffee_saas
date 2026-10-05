from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.core.tenant import TenantContext
from app.db.session import get_db_session
from app.schemas.branch import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
)
from app.services.branch import BranchService


router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
)


@router.get(
    "",
    response_model=list[BranchResponse],
)
async def list_branches(
    tenant: TenantContext = Depends(
        require_permission("branches.read")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> list[BranchResponse]:
    branches = await BranchService.list_branches(
        session=session,
        tenant=tenant,
    )

    return [
        BranchResponse.model_validate(branch)
        for branch in branches
    ]


@router.get(
    "/{branch_id}",
    response_model=BranchResponse,
)
async def get_branch(
    branch_id: UUID,
    tenant: TenantContext = Depends(
        require_permission("branches.read")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> BranchResponse:
    branch = await BranchService.get_branch(
        session=session,
        tenant=tenant,
        branch_id=branch_id,
    )

    if branch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )

    return BranchResponse.model_validate(branch)


@router.post(
    "",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_branch(
    payload: BranchCreate,
    tenant: TenantContext = Depends(
        require_permission("branches.create")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> BranchResponse:
    try:
        branch = await BranchService.create_branch(
            session=session,
            tenant=tenant,
            data=payload,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch code already exists in this organization",
        )

    return BranchResponse.model_validate(branch)


@router.patch(
    "/{branch_id}",
    response_model=BranchResponse,
)
async def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    tenant: TenantContext = Depends(
        require_permission("branches.update")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> BranchResponse:
    try:
        branch = await BranchService.update_branch(
            session=session,
            tenant=tenant,
            branch_id=branch_id,
            data=payload,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch code already exists in this organization",
        )

    if branch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )

    return BranchResponse.model_validate(branch)


@router.delete(
    "/{branch_id}",
    response_model=BranchResponse,
)
async def delete_branch(
    branch_id: UUID,
    tenant: TenantContext = Depends(
        require_permission("branches.delete")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> BranchResponse:
    branch = await BranchService.delete_branch(
        session=session,
        tenant=tenant,
        branch_id=branch_id,
    )

    if branch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )

    return BranchResponse.model_validate(branch)