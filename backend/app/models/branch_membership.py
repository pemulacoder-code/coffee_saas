from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.role import Role
    from app.models.user import User


class BranchMembership(BaseModel):
    __tablename__ = "branch_memberships"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    branch_id: Mapped[UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="branch_memberships",
    )

    branch: Mapped["Branch"] = relationship(
        back_populates="memberships",
    )

    role: Mapped["Role | None"] = relationship(
        back_populates="branch_memberships",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "branch_id",
            name="uq_branch_memberships_user_branch",
        ),
    )