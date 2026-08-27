from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


PREVIOUS_REVISION = "d3a8f6c41b29"
TRIP_REVISION = "c6e2a9b47f31"
HEAD_REVISION = "7b5f24c91a10"
BACKEND_DIR = Path(__file__).resolve().parents[3]


def test_trip_migration_upgrade_downgrade_upgrade() -> None:
    raw_url = os.getenv("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    url = make_url(raw_url)
    database_name = (url.database or "").lower()
    if not url.drivername.startswith("postgresql") or not any(
        marker in database_name for marker in ("test", "testing", "ci")
    ):
        pytest.skip("Refusing to use a non-isolated PostgreSQL test database")

    environment = os.environ.copy()
    environment["DATABASE_URL"] = raw_url
    environment["TEST_DATABASE_URL"] = raw_url

    def alembic(*arguments: str) -> None:
        subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=BACKEND_DIR,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

    engine = create_engine(raw_url, pool_pre_ping=True)
    try:
        alembic("upgrade", "head")
        inspector = inspect(engine)
        assert {"trips", "trip_items"}.issubset(inspector.get_table_names())
        assert {"user_id", "title", "start_date", "end_date", "status", "visibility", "share_token", "version"}.issubset(
            column["name"] for column in inspector.get_columns("trips")
        )
        assert {"trip_id", "destination_id", "day_number", "sort_order"}.issubset(
            column["name"] for column in inspector.get_columns("trip_items")
        )
        trip_indexes = {index["name"] for index in inspector.get_indexes("trips")}
        assert "ux_trips_share_token" in trip_indexes

        indexes = {index["name"] for index in inspector.get_indexes("trip_items")}
        assert {
            "ix_trip_items_destination_id",
            "ix_trip_items_trip_id",
            "ix_trip_items_trip_day_order",
        }.issubset(indexes)
        uniques = {item["name"] for item in inspector.get_unique_constraints("trip_items")}
        assert "uq_trip_items_trip_destination_day" not in uniques
        assert "uq_trip_items_trip_day_position" in uniques
        foreign_keys = {fk["constrained_columns"][0]: fk for fk in inspector.get_foreign_keys("trip_items")}
        assert foreign_keys["trip_id"]["options"].get("ondelete") == "CASCADE"
        assert foreign_keys["destination_id"]["options"].get("ondelete") == "CASCADE"
        trip_foreign_keys = inspector.get_foreign_keys("trips")
        assert len(trip_foreign_keys) == 1
        assert trip_foreign_keys[0]["options"].get("ondelete") == "CASCADE"
        trip_checks = {check["name"] for check in inspector.get_check_constraints("trips")}
        item_checks = {check["name"] for check in inspector.get_check_constraints("trip_items")}
        assert "ck_trips_trip_date_range" in trip_checks
        assert {
            "ck_trip_items_day_number_positive",
            "ck_trip_items_sort_order_nonnegative",
            "ck_trip_items_duration_minutes_positive",
        }.issubset(item_checks)

        with engine.begin() as connection:
            user_id = connection.scalar(text("""
                INSERT INTO users (full_name, email, username, hashed_password)
                VALUES ('Trip Migration', 'trip-migration@example.com', 'trip-migration', 'hash')
                RETURNING id
            """))
            destination_id = connection.scalar(text("""
                INSERT INTO destinations (slug, status)
                VALUES ('trip-migration-destination', 'published') RETURNING id
            """))
            second_destination_id = connection.scalar(text("""
                INSERT INTO destinations (slug, status)
                VALUES ('trip-migration-second-destination', 'published') RETURNING id
            """))
            trip_id = connection.scalar(text("""
                INSERT INTO trips (user_id, title, start_date, end_date)
                VALUES (:user_id, 'Test', '2026-09-01', '2026-09-03') RETURNING id
            """), {"user_id": user_id})
            connection.execute(text("""
                INSERT INTO trip_items (trip_id, destination_id, day_number)
                VALUES (:trip_id, :destination_id, 1)
            """), {"trip_id": trip_id, "destination_id": destination_id})
            connection.execute(text("""
                INSERT INTO trip_items (
                    trip_id,
                    destination_id,
                    day_number,
                    sort_order
                )
                VALUES (
                    :trip_id,
                    :destination_id,
                    1,
                    1
                )
            """), {
                "trip_id": trip_id,
                "destination_id": destination_id,
            })
            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO trip_items (
                            trip_id, destination_id, day_number, sort_order
                        ) VALUES (:trip_id, :destination_id, 1, 0)
                    """), {
                        "trip_id": trip_id,
                        "destination_id": second_destination_id,
                    })
            assert connection.scalar(
                text("SELECT version FROM trips WHERE id = :id"),
                {"id": trip_id},
            ) == 1
            connection.execute(text("DELETE FROM trips WHERE id = :id"), {"id": trip_id})
            assert connection.scalar(text("SELECT count(*) FROM trip_items WHERE trip_id = :id"), {"id": trip_id}) == 0
            connection.execute(text("DELETE FROM destinations WHERE id = :id"), {"id": destination_id})
            connection.execute(
                text("DELETE FROM destinations WHERE id = :id"),
                {"id": second_destination_id},
            )
            connection.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})

        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION

        alembic("downgrade", PREVIOUS_REVISION)
        inspector = inspect(engine)
        assert "trip_items" not in inspector.get_table_names()
        assert "trips" not in inspector.get_table_names()
        alembic("upgrade", "head")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION
    finally:
        engine.dispose()
