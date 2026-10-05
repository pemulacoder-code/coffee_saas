"""add branch management permissions

Revision ID: 3c7269abc144
Revises: c5f892e68f1d
Create Date: 2026-10-04
"""

from datetime import datetime, timezone
from uuid import UUID, uuid5

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3c7269abc144"
down_revision = "c5f892e68f1d"
branch_labels = None
depends_on = None


PERMISSION_NAMESPACE = UUID("10000000-0000-0000-0000-000000000000")
ROLE_PERMISSION_NAMESPACE = UUID("20000000-0000-0000-0000-000000000000")

OWNER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")
ADMIN_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")

PERMISSIONS = [
    {
        "id": UUID("10000000-0000-0000-0000-00000000001a"),
        "name": "Read branches",
        "code": "branches.read",
        "description": "View branches within the organization.",
    },
    {
        "id": UUID("10000000-0000-0000-0000-00000000001b"),
        "name": "Create branches",
        "code": "branches.create",
        "description": "Create branches within the organization.",
    },
    {
        "id": UUID("10000000-0000-0000-0000-00000000001c"),
        "name": "Update branches",
        "code": "branches.update",
        "description": "Update branches within the organization.",
    },
    {
        "id": UUID("10000000-0000-0000-0000-00000000001d"),
        "name": "Delete branches",
        "code": "branches.delete",
        "description": "Deactivate or delete branches within the organization.",
    },
]


def _role_permission_id(role_id: UUID, permission_id: UUID) -> UUID:
    return uuid5(
        ROLE_PERMISSION_NAMESPACE,
        f"{role_id}:{permission_id}",
    )


def upgrade() -> None:
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)

    op.bulk_insert(
        permissions_table,
        [
            {
                **permission,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for permission in PERMISSIONS
        ],
    )

    role_permission_rows = []

    for role_id in (OWNER_ROLE_ID, ADMIN_ROLE_ID):
        for permission in PERMISSIONS:
            role_permission_rows.append(
                {
                    "id": _role_permission_id(role_id, permission["id"]),
                    "role_id": role_id,
                    "permission_id": permission["id"],
                    "created_at": now,
                    "updated_at": now,
                }
            )

    op.bulk_insert(
        role_permissions_table,
        role_permission_rows,
    )


def downgrade() -> None:
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
    )

    permission_ids = [permission["id"] for permission in PERMISSIONS]

    role_permission_ids = [
        _role_permission_id(role_id, permission_id)
        for role_id in (OWNER_ROLE_ID, ADMIN_ROLE_ID)
        for permission_id in permission_ids
    ]

    op.execute(
        role_permissions_table.delete().where(
            role_permissions_table.c.id.in_(role_permission_ids)
        )
    )

    op.execute(
        permissions_table.delete().where(
            permissions_table.c.id.in_(permission_ids)
        )
    )