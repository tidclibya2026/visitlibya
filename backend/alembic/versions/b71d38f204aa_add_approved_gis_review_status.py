"""add approved governed GIS review status

Revision ID: b71d38f204aa
Revises: 8d4e2c7a1f60
"""
from alembic import op


revision = "b71d38f204aa"
down_revision = "8d4e2c7a1f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "governed_gis_review_status", "governed_gis_features", type_="check"
    )
    op.create_check_constraint(
        "governed_gis_review_status",
        "governed_gis_features",
        "review_status IN ('draft', 'under_review', 'reviewed', 'approved')",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE governed_gis_features SET review_status = 'reviewed' "
        "WHERE review_status = 'approved'"
    )
    op.drop_constraint(
        "governed_gis_review_status", "governed_gis_features", type_="check"
    )
    op.create_check_constraint(
        "governed_gis_review_status",
        "governed_gis_features",
        "review_status IN ('draft', 'under_review', 'reviewed')",
    )
