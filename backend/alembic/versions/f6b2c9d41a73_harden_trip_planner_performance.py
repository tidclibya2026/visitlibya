"""harden trip planner performance and concurrency

Revision ID: f6b2c9d41a73
Revises: e8c4b7a29f10
Create Date: 2026-07-22 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f6b2c9d41a73"
down_revision: str | Sequence[str] | None = "e8c4b7a29f10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )

    # Fail explicitly if historical data cannot satisfy the new concurrency
    # guarantee. Re-numbering silently would change user-authored ordering.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM trip_items
                GROUP BY trip_id, day_number, sort_order
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Cannot add uq_trip_items_trip_day_position: duplicate trip item positions exist';
            END IF;
        END
        $$;
        """
    )
    op.create_unique_constraint(
        "uq_trip_items_trip_day_position",
        "trip_items",
        ["trip_id", "day_number", "sort_order"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_trip_items_trip_day_position",
        "trip_items",
        type_="unique",
    )
    op.drop_column("trips", "version")

