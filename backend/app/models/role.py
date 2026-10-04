from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.branch_membership import BranchMembership
    from app.models.organization_membership import OrganizationMembership
    from app.models.role_permission import RolePermission


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role",
    )

    organization_memberships: Mapped[
        list["OrganizationMembership"]
    ] = relationship(
        back_populates="role",
    )

    branch_memberships: Mapped[
        list["BranchMembership"]
    ] = relationship(
        back_populates="role",
    )