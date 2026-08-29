from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON, Boolean, CheckConstraint, DateTime, Enum, Index, Integer, String,
    Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class GISReviewStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class GISAuthorityStatus(str, enum.Enum):
    UNAPPROVED = "unapproved"
    APPROVED = "approved"
    REJECTED = "rejected"


class GISValidationStatus(str, enum.Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class GovernedGISFeature(TimestampMixin, Base):
    __tablename__ = "governed_gis_features"
    __table_args__ = (
        UniqueConstraint("layer_code", "feature_code", name="uq_governed_gis_layer_feature"),
        UniqueConstraint(
            "layer_code", "institutional_id", name="uq_governed_gis_layer_institutional"
        ),
        CheckConstraint(
            "GeometryType(geometry) IN ('POINT', 'MULTIPOINT', 'LINESTRING', "
            "'MULTILINESTRING', 'POLYGON', 'MULTIPOLYGON')",
            name="governed_gis_geometry_supported",
        ),
        CheckConstraint("ST_SRID(geometry) = 4326", name="governed_gis_geometry_srid"),
        CheckConstraint("ST_IsValid(geometry)", name="governed_gis_geometry_valid"),
        CheckConstraint(
            "geometry_type = GeometryType(geometry)", name="governed_gis_geometry_type_matches"
        ),
        CheckConstraint(
            "NOT is_published OR (is_validated AND validation_status = 'valid' "
            "AND authority_status = 'approved')",
            name="governed_gis_publication_gate",
        ),
        Index("idx_governed_gis_geometry", "geometry", postgresql_using="gist"),
        Index("ix_governed_gis_layer_code", "layer_code"),
        Index("ix_governed_gis_is_published", "is_published"),
        Index("ix_governed_gis_public_layer", "layer_code", "is_published"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institutional_id: Mapped[str] = mapped_column(String(250), nullable=False)
    layer_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_code: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(250), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(250), nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=False
    )
    geometry_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_owner: Mapped[str] = mapped_column(String(250), nullable=False)
    institutional_reference: Mapped[str] = mapped_column(String(250), nullable=False)
    source_database: Mapped[str | None] = mapped_column(String(250), nullable=True)
    source_layer: Mapped[str] = mapped_column(String(250), nullable=False)
    source_feature_id: Mapped[str] = mapped_column(String(250), nullable=False)
    source_filter: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_identity: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_geometry_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    review_status: Mapped[GISReviewStatus] = mapped_column(
        Enum(GISReviewStatus, name="gis_review_status", native_enum=False, length=30,
             values_callable=lambda enum_class: [item.value for item in enum_class]),
        default=GISReviewStatus.DRAFT, server_default=GISReviewStatus.DRAFT.value,
        nullable=False,
    )
    authority_status: Mapped[GISAuthorityStatus] = mapped_column(
        Enum(GISAuthorityStatus, name="gis_authority_status", native_enum=False, length=30,
             values_callable=lambda enum_class: [item.value for item in enum_class]),
        default=GISAuthorityStatus.UNAPPROVED,
        server_default=GISAuthorityStatus.UNAPPROVED.value, nullable=False,
    )
    validation_status: Mapped[GISValidationStatus] = mapped_column(
        Enum(GISValidationStatus, name="gis_validation_status", native_enum=False, length=30,
             values_callable=lambda enum_class: [item.value for item in enum_class]),
        default=GISValidationStatus.PENDING,
        server_default=GISValidationStatus.PENDING.value, nullable=False,
    )
    is_validated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

