from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NationalBoundary(TimestampMixin, Base):
    __tablename__ = "national_boundaries"

    __table_args__ = (
        Index(
            "idx_national_boundaries_geometry",
            "geometry",
            postgresql_using="gist",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        unique=True,
        index=True,
        nullable=False,
    )

    name_en: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    name_ar: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    source_owner: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    institutional_reference: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    source_database: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    source_feature_dataset: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    source_feature_class: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    source_filter: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    source_name_en: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    source_name_ar: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    source_geometry_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    source_metadata: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )

    is_validated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
        nullable=False,
    )
