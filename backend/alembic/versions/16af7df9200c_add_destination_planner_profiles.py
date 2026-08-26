"""add destination planner profiles

Revision ID: 16af7df9200c
Revises: a4902527f045
Create Date: 2026-08-26 14:08:01.283430
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "16af7df9200c"
down_revision: str | Sequence[str] | None = "a4902527f045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "destination_planner_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),

        sa.Column(
            "recommended_visit_minutes",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "minimum_visit_minutes",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "maximum_visit_minutes",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "opening_hours",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "opening_hours_timezone",
            sa.String(length=100),
            server_default="Africa/Tripoli",
            nullable=False,
        ),

        sa.Column(
            "access_status",
            sa.String(length=20),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "road_access",
            sa.String(length=30),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "road_surface",
            sa.String(length=20),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "road_condition",
            sa.String(length=20),
            server_default="unknown",
            nullable=False,
        ),

        sa.Column(
            "planner_priority",
            sa.Integer(),
            server_default="50",
            nullable=False,
        ),
        sa.Column(
            "meal_suitability",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "rest_suitability",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),

        sa.Column(
            "data_source",
            sa.String(length=250),
            nullable=True,
        ),
        sa.Column(
            "verification_status",
            sa.String(length=20),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.CheckConstraint(
            "recommended_visit_minutes IS NULL "
            "OR recommended_visit_minutes > 0",
            name="destination_planner_recommended_visit_positive",
        ),
        sa.CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR minimum_visit_minutes > 0",
            name="destination_planner_minimum_visit_positive",
        ),
        sa.CheckConstraint(
            "maximum_visit_minutes IS NULL "
            "OR maximum_visit_minutes > 0",
            name="destination_planner_maximum_visit_positive",
        ),
        sa.CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR recommended_visit_minutes IS NULL "
            "OR minimum_visit_minutes <= recommended_visit_minutes",
            name="destination_planner_minimum_not_above_recommended",
        ),
        sa.CheckConstraint(
            "maximum_visit_minutes IS NULL "
            "OR recommended_visit_minutes IS NULL "
            "OR maximum_visit_minutes >= recommended_visit_minutes",
            name="destination_planner_maximum_not_below_recommended",
        ),
        sa.CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR maximum_visit_minutes IS NULL "
            "OR minimum_visit_minutes <= maximum_visit_minutes",
            name="destination_planner_visit_range_valid",
        ),
        sa.CheckConstraint(
            "planner_priority >= 0 AND planner_priority <= 100",
            name="destination_planner_priority_range",
        ),
        sa.CheckConstraint(
            "meal_suitability >= 0 AND meal_suitability <= 100",
            name="destination_planner_meal_suitability_range",
        ),
        sa.CheckConstraint(
            "rest_suitability >= 0 AND rest_suitability <= 100",
            name="destination_planner_rest_suitability_range",
        ),

        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["destinations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "destination_id",
            name="uq_destination_planner_profile_destination",
        ),
    )

    op.create_index(
        "ix_destination_planner_profiles_destination_id",
        "destination_planner_profiles",
        ["destination_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_destination_planner_profiles_destination_id",
        table_name="destination_planner_profiles",
    )
    op.drop_table("destination_planner_profiles")
