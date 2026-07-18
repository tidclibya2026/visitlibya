from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.destination import Destination


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        unique=True,
        nullable=False,
    )

    public_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    alt_ar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    alt_en: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    caption_ar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    caption_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    photographer: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    copyright_owner: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    usage_rights: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    destination_links: Mapped[list["DestinationMedia"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DestinationMedia(TimestampMixin, Base):
    __tablename__ = "destination_media"

    __table_args__ = (
        UniqueConstraint(
            "destination_id",
            "media_id",
            name="uq_destination_media_link",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    destination: Mapped["Destination"] = relationship(
        back_populates="media_items",
    )

    media: Mapped["MediaAsset"] = relationship(
        back_populates="destination_links",
        lazy="joined",
    )