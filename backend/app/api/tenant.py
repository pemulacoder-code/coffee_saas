from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_tenant
from app.core.tenant import TenantContext


router = APIRouter(
    prefix="/tenant",
    tags=["Tenant"],
)


@router.get("")
async def get_tenant(
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict[str, str]:
    return {
        "organization_id": str(tenant.organization_id),
    }