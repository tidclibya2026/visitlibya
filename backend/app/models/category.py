from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.destination import Destination


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    name_ar: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    name_en: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description_ar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    destinations: Mapped[list["Destination"]] = relationship(
        back_populates="category",
        lazy="selectin",
    )