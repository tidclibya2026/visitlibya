"""add planner runs authority foundation

Revision ID: a4902527f045
Revises: c6e2a9b47f31
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a4902527f045"
down_revision: str | Sequence[str] | None = "c6e2a9b47f31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "planner_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "planner_version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "engine_version",
            sa.String(length=64),
            server_default="visitlibya-ai-planner-v1",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="generated",
            nullable=False,
        ),
        sa.Column(
            "feasibility_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "input_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "itinerary_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "feasibility_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "recommendations_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "optimization_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
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
            "planner_version >= 1",
            name="planner_run_version_positive",
        ),
        sa.CheckConstraint(
            "feasibility_score IS NULL OR "
            "(feasibility_score >= 0 "
            "AND feasibility_score <= 100)",
            name="planner_run_feasibility_range",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_planner_runs_trip_created_at",
        "planner_runs",
        ["trip_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_planner_runs_user_created_at",
        "planner_runs",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_planner_runs_user_created_at",
        table_name="planner_runs",
    )
    op.drop_index(
        "ix_planner_runs_trip_created_at",
        table_name="planner_runs",
    )
    op.drop_table("planner_runs")
