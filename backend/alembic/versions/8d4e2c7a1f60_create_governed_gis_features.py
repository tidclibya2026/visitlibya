"""create reusable governed GIS feature authority

Revision ID: 8d4e2c7a1f60
Revises: 7b5f24c91a10
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8d4e2c7a1f60"
down_revision: str | None = "7b5f24c91a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "governed_gis_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institutional_id", sa.String(length=250), nullable=False),
        sa.Column("layer_code", sa.String(length=100), nullable=False),
        sa.Column("feature_code", sa.String(length=200), nullable=False),
        sa.Column("name_ar", sa.String(length=250), nullable=True),
        sa.Column("name_en", sa.String(length=250), nullable=True),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="GEOMETRY", srid=4326, spatial_index=False
            ),
            nullable=False,
        ),
        sa.Column("geometry_type", sa.String(length=30), nullable=False),
        sa.Column("source_owner", sa.String(length=250), nullable=False),
        sa.Column("institutional_reference", sa.String(length=250), nullable=False),
        sa.Column("source_database", sa.String(length=250), nullable=True),
        sa.Column("source_layer", sa.String(length=250), nullable=False),
        sa.Column("source_feature_id", sa.String(length=250), nullable=False),
        sa.Column("source_filter", sa.String(length=500), nullable=True),
        sa.Column("source_identity", sa.String(length=500), nullable=True),
        sa.Column("source_geometry_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "source_metadata", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"), nullable=False,
        ),
        sa.Column("review_status", sa.String(length=30), server_default="draft", nullable=False),
        sa.Column(
            "authority_status", sa.String(length=30), server_default="unapproved", nullable=False
        ),
        sa.Column(
            "validation_status", sa.String(length=30), server_default="pending", nullable=False
        ),
        sa.Column("is_validated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "review_status IN ('draft', 'under_review', 'reviewed')",
            name="governed_gis_review_status",
        ),
        sa.CheckConstraint(
            "authority_status IN ('unapproved', 'approved', 'rejected')",
            name="governed_gis_authority_status",
        ),
        sa.CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid')",
            name="governed_gis_validation_status",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POINT', 'MULTIPOINT', 'LINESTRING', "
            "'MULTILINESTRING', 'POLYGON', 'MULTIPOLYGON')",
            name="governed_gis_geometry_supported",
        ),
        sa.CheckConstraint("ST_SRID(geometry) = 4326", name="governed_gis_geometry_srid"),
        sa.CheckConstraint("ST_IsValid(geometry)", name="governed_gis_geometry_valid"),
        sa.CheckConstraint(
            "geometry_type = GeometryType(geometry)",
            name="governed_gis_geometry_type_matches",
        ),
        sa.CheckConstraint(
            "NOT is_published OR (is_validated AND validation_status = 'valid' "
            "AND authority_status = 'approved')",
            name="governed_gis_publication_gate",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("layer_code", "feature_code", name="uq_governed_gis_layer_feature"),
        sa.UniqueConstraint(
            "layer_code", "institutional_id", name="uq_governed_gis_layer_institutional"
        ),
    )
    op.create_index("ix_governed_gis_layer_code", "governed_gis_features", ["layer_code"])
    op.create_index("ix_governed_gis_is_published", "governed_gis_features", ["is_published"])
    op.create_index(
        "ix_governed_gis_public_layer", "governed_gis_features",
        ["layer_code", "is_published"],
    )
    op.create_index(
        "idx_governed_gis_geometry", "governed_gis_features", ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("idx_governed_gis_geometry", table_name="governed_gis_features")
    op.drop_index("ix_governed_gis_public_layer", table_name="governed_gis_features")
    op.drop_index("ix_governed_gis_is_published", table_name="governed_gis_features")
    op.drop_index("ix_governed_gis_layer_code", table_name="governed_gis_features")
    op.drop_table("governed_gis_features")
