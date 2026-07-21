"""create favorites table

Revision ID: d3a8f6c41b29
Revises: b7f4a2c91d30
Create Date: 2026-07-20 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d3a8f6c41b29"
down_revision: str | Sequence[str] | None = "b7f4a2c91d30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["destinations.id"],
            name=op.f("fk_favorites_destination_id_destinations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_favorites_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint(
            "user_id",
            "destination_id",
            name="uq_favorites_user_destination",
        ),
    )
    op.create_index(
        op.f("ix_favorites_destination_id"),
        "favorites",
        ["destination_id"],
    )
    op.create_index(
        "ix_favorites_user_created_at",
        "favorites",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_favorites_user_created_at", table_name="favorites")
    op.drop_index(op.f("ix_favorites_destination_id"), table_name="favorites")
    op.drop_table("favorites")
