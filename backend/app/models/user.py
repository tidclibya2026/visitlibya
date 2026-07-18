from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )