"""create trip planner tables

Revision ID: e8c4b7a29f10
Revises: d3a8f6c41b29
Create Date: 2026-07-21 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8c4b7a29f10"
down_revision: str | Sequence[str] | None = "d3a8f6c41b29"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("visibility", sa.String(length=20), server_default="private", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name=op.f("ck_trips_trip_date_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_trips_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trips")),
    )
    op.create_index("ix_trips_user_created_at", "trips", ["user_id", "created_at"])
    op.create_index("ix_trips_user_start_date", "trips", ["user_id", "start_date"])

    op.create_table(
        "trip_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("day_number >= 1", name=op.f("ck_trip_items_day_number_positive")),
        sa.CheckConstraint("sort_order >= 0", name=op.f("ck_trip_items_sort_order_nonnegative")),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name=op.f("ck_trip_items_duration_minutes_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["destinations.id"],
            name=op.f("fk_trip_items_destination_id_destinations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name=op.f("fk_trip_items_trip_id_trips"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_items")),
        sa.UniqueConstraint(
            "trip_id",
            "destination_id",
            "day_number",
            name="uq_trip_items_trip_destination_day",
        ),
    )
    op.create_index(op.f("ix_trip_items_destination_id"), "trip_items", ["destination_id"])
    op.create_index(op.f("ix_trip_items_trip_id"), "trip_items", ["trip_id"])
    op.create_index(
        "ix_trip_items_trip_day_order",
        "trip_items",
        ["trip_id", "day_number", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_items_trip_day_order", table_name="trip_items")
    op.drop_index(op.f("ix_trip_items_trip_id"), table_name="trip_items")
    op.drop_index(op.f("ix_trip_items_destination_id"), table_name="trip_items")
    op.drop_table("trip_items")
    op.drop_index("ix_trips_user_start_date", table_name="trips")
    op.drop_index("ix_trips_user_created_at", table_name="trips")
    op.drop_table("trips")
