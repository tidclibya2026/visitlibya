"""backfill destination postgis geometry

Revision ID: 3ce91b819d4a
Revises: 16af7df9200c
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op


revision: str = "3ce91b819d4a"
down_revision: str | None = "16af7df9200c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Populate existing PostGIS geometry from valid legacy coordinates."""

    op.execute(
        """
        UPDATE destinations
        SET geometry = ST_SetSRID(
            ST_MakePoint(longitude, latitude),
            4326
        )
        WHERE longitude IS NOT NULL
          AND latitude IS NOT NULL
          AND longitude BETWEEN -180 AND 180
          AND latitude BETWEEN -90 AND 90
          AND geometry IS NULL
        """
    )


def downgrade() -> None:
    """Preserve spatial data during downgrade.

    Geometry is part of the original destination schema, so this migration
    must not remove the column, spatial index, PostGIS extension, or values.
    """
    pass
