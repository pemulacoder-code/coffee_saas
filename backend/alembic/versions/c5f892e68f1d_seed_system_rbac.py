"""seed system rbac

Revision ID: REPLACE_WITH_GENERATED_REVISION
Revises: 1bc47d34cd64
Create Date: 2026-10-04
"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import UUID, uuid5

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5f892e68f1d'
down_revision: Union[str, Sequence[str], None] = '1bc47d34cd64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_IDS = {
    "owner": UUID("00000000-0000-0000-0000-000000000001"),
    "admin": UUID("00000000-0000-0000-0000-000000000002"),
    "cashier": UUID("00000000-0000-0000-0000-000000000003"),
    "barista": UUID("00000000-0000-0000-0000-000000000004"),
    "kitchen": UUID("00000000-0000-0000-0000-000000000005"),
}


PERMISSION_IDS = {
    "users.read": UUID("10000000-0000-0000-0000-000000000001"),
    "users.create": UUID("10000000-0000-0000-0000-000000000002"),
    "users.update": UUID("10000000-0000-0000-0000-000000000003"),
    "memberships.read": UUID("10000000-0000-0000-0000-000000000004"),
    "memberships.create": UUID("10000000-0000-0000-0000-000000000005"),
    "memberships.update": UUID("10000000-0000-0000-0000-000000000006"),
    "memberships.delete": UUID("10000000-0000-0000-0000-000000000007"),
    "products.read": UUID("10000000-0000-0000-0000-000000000008"),
    "products.create": UUID("10000000-0000-0000-0000-000000000009"),
    "products.update": UUID("10000000-0000-0000-0000-000000000010"),
    "products.delete": UUID("10000000-0000-0000-0000-000000000011"),
    "orders.read": UUID("10000000-0000-0000-0000-000000000012"),
    "orders.create": UUID("10000000-0000-0000-0000-000000000013"),
    "orders.update": UUID("10000000-0000-0000-0000-000000000014"),
    "orders.cancel": UUID("10000000-0000-0000-0000-000000000015"),
    "pos.access": UUID("10000000-0000-0000-0000-000000000016"),
    "reports.read": UUID("10000000-0000-0000-0000-000000000017"),
    "settings.read": UUID("10000000-0000-0000-0000-000000000018"),
    "settings.update": UUID("10000000-0000-0000-0000-000000000019"),
}


ALL_PERMISSIONS = list(PERMISSION_IDS.keys())


ROLE_PERMISSIONS = {
    "owner": ALL_PERMISSIONS,
    "admin": ALL_PERMISSIONS,
    "cashier": [
        "products.read",
        "orders.read",
        "orders.create",
        "pos.access",
    ],
    "barista": [
        "products.read",
        "orders.read",
        "orders.update",
    ],
    "kitchen": [
        "products.read",
        "orders.read",
        "orders.update",
    ],
}


ROLE_PERMISSION_NAMESPACE = UUID(
    "20000000-0000-0000-0000-000000000000"
)


def upgrade() -> None:
    """Seed system roles, permissions, and role permissions."""

    now = datetime.now(timezone.utc)

    roles = sa.table(
        "roles",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_system", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    role_permissions = sa.table(
        "role_permissions",
        sa.column("id", sa.UUID()),
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        roles,
        [
            {
                "id": role_id,
                "name": code.replace("_", " ").title(),
                "code": code,
                "description": f"System role: {code}",
                "is_system": True,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for code, role_id in ROLE_IDS.items()
        ],
    )

    op.bulk_insert(
        permissions,
        [
            {
                "id": permission_id,
                "name": code.replace(".", " ").title(),
                "code": code,
                "description": f"Permission: {code}",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for code, permission_id in PERMISSION_IDS.items()
        ],
    )

    role_permission_rows = []

    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
            role_permission_rows.append(
                {
                    "id": uuid5(
                        ROLE_PERMISSION_NAMESPACE,
                        f"{role_code}:{permission_code}",
                    ),
                    "role_id": ROLE_IDS[role_code],
                    "permission_id": PERMISSION_IDS[permission_code],
                    "created_at": now,
                    "updated_at": now,
                }
            )

    op.bulk_insert(
        role_permissions,
        role_permission_rows,
    )


def downgrade() -> None:
    """Remove system RBAC seed data."""

    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE role_id IN (
                :owner,
                :admin,
                :cashier,
                :barista,
                :kitchen
            )
            """
        ),
        {
            "owner": ROLE_IDS["owner"],
            "admin": ROLE_IDS["admin"],
            "cashier": ROLE_IDS["cashier"],
            "barista": ROLE_IDS["barista"],
            "kitchen": ROLE_IDS["kitchen"],
        },
    )

    connection.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE id IN (
                :users_read,
                :users_create,
                :users_update,
                :memberships_read,
                :memberships_create,
                :memberships_update,
                :memberships_delete,
                :products_read,
                :products_create,
                :products_update,
                :products_delete,
                :orders_read,
                :orders_create,
                :orders_update,
                :orders_cancel,
                :pos_access,
                :reports_read,
                :settings_read,
                :settings_update
            )
            """
        ),
        {
            key.replace(".", "_"): value
            for key, value in PERMISSION_IDS.items()
        },
    )

    connection.execute(
        sa.text(
            """
            DELETE FROM roles
            WHERE id IN (
                :owner,
                :admin,
                :cashier,
                :barista,
                :kitchen
            )
            """
        ),
        {
            "owner": ROLE_IDS["owner"],
            "admin": ROLE_IDS["admin"],
            "cashier": ROLE_IDS["cashier"],
            "barista": ROLE_IDS["barista"],
            "kitchen": ROLE_IDS["kitchen"],
        },
    )