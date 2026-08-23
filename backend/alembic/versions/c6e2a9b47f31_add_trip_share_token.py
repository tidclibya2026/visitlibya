"""add trip share token

Revision ID: c6e2a9b47f31
Revises: a1c7e4f92b10
Create Date: 2026-08-23 22:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c6e2a9b47f31"
down_revision: str | Sequence[str] | None = "a1c7e4f92b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("share_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ux_trips_share_token",
        "trips",
        ["share_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_trips_share_token", table_name="trips")
    op.drop_column("trips", "share_token")
