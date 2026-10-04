from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    organization_id: UUID