"""allow duplicate destinations within trips

Revision ID: a1c7e4f92b10
Revises: f6b2c9d41a73
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "a1c7e4f92b10"
down_revision: str | Sequence[str] | None = "f6b2c9d41a73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_trip_items_trip_destination_day",
        "trip_items",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_trip_items_trip_destination_day",
        "trip_items",
        ["trip_id", "destination_id", "day_number"],
    )
