"""create governed national boundaries

Revision ID: 7b5f24c91a10
Revises: 3ce91b819d4a
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op
import geoalchemy2
import sqlalchemy as sa


revision: str = "7b5f24c91a10"
down_revision: str | None = "3ce91b819d4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "national_boundaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("name_en", sa.String(length=150), nullable=False),
        sa.Column("name_ar", sa.String(length=150), nullable=False),
        sa.Column("source_owner", sa.String(length=250), nullable=False),
        sa.Column(
            "institutional_reference",
            sa.String(length=250),
            nullable=False,
        ),
        sa.Column(
            "source_database",
            sa.String(length=250),
            nullable=False,
        ),
        sa.Column(
            "source_feature_dataset",
            sa.String(length=250),
            nullable=False,
        ),
        sa.Column(
            "source_feature_class",
            sa.String(length=250),
            nullable=False,
        ),
        sa.Column(
            "source_filter",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "source_name_en",
            sa.String(length=250),
            nullable=True,
        ),
        sa.Column(
            "source_name_ar",
            sa.String(length=250),
            nullable=True,
        ),
        sa.Column(
            "source_geometry_sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "source_metadata",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_validated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code"),
    )

    op.create_index(
        "ix_national_boundaries_country_code",
        "national_boundaries",
        ["country_code"],
        unique=True,
    )

    op.create_index(
        "ix_national_boundaries_is_published",
        "national_boundaries",
        ["is_published"],
        unique=False,
    )

    op.create_index(
        "idx_national_boundaries_geometry",
        "national_boundaries",
        ["geometry"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_check_constraint(
        "ck_national_boundaries_geometry_valid",
        "national_boundaries",
        "ST_IsValid(geometry)",
    )

    op.create_check_constraint(
        "ck_national_boundaries_geometry_srid",
        "national_boundaries",
        "ST_SRID(geometry) = 4326",
    )

    op.create_check_constraint(
        "ck_national_boundaries_geometry_type",
        "national_boundaries",
        "GeometryType(geometry) = 'MULTIPOLYGON'",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_national_boundaries_geometry",
        table_name="national_boundaries",
    )
    op.drop_index(
        "ix_national_boundaries_is_published",
        table_name="national_boundaries",
    )
    op.drop_index(
        "ix_national_boundaries_country_code",
        table_name="national_boundaries",
    )
    op.drop_table("national_boundaries")
