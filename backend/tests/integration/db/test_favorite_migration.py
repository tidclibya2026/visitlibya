from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError


PREVIOUS_REVISION = "b7f4a2c91d30"
FAVORITES_REVISION = "d3a8f6c41b29"

BACKEND_DIR = Path(__file__).resolve().parents[3]


def _test_database_url() -> str:
    """
    Return a PostgreSQL URL that is explicitly intended for automated testing.

    The test is skipped unless TEST_DATABASE_URL is configured. As an additional
    safety check, the database name must contain either "test" or "ci".
    """
    raw_url = os.getenv("TEST_DATABASE_URL")

    if not raw_url:
        pytest.skip(
            "TEST_DATABASE_URL is not configured; "
            "live PostgreSQL migration test was skipped."
        )

    url = make_url(raw_url)

    if not url.drivername.startswith("postgresql"):
        pytest.skip(
            "TEST_DATABASE_URL must point to a PostgreSQL/PostGIS database."
        )

    database_name = (url.database or "").lower()

    if "test" not in database_name and "ci" not in database_name:
        pytest.skip(
            "Refusing to run migration test because the database name does not "
            "contain 'test' or 'ci'."
        )

    return raw_url


def _alembic(database_url: str, *arguments: str) -> None:
    """
    Run Alembic in a subprocess against the isolated test database.

    Both DATABASE_URL and TEST_DATABASE_URL are supplied because the application
    configuration may read DATABASE_URL while this test is guarded by
    TEST_DATABASE_URL.
    """
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment["TEST_DATABASE_URL"] = database_url

    result = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Alembic command failed.\n"
            f"Command: alembic {' '.join(arguments)}\n"
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def _assert_favorites_schema(engine: Engine) -> None:
    """
    Verify the favorites table, columns, constraints, indexes, and cascade rules.
    """
    inspector = inspect(engine)

    assert "favorites" in inspector.get_table_names()

    columns = {
        column["name"]: column
        for column in inspector.get_columns("favorites")
    }

    assert set(columns) == {
        "id",
        "user_id",
        "destination_id",
        "created_at",
    }

    assert columns["id"]["nullable"] is False
    assert columns["user_id"]["nullable"] is False
    assert columns["destination_id"]["nullable"] is False
    assert columns["created_at"]["nullable"] is False

    # PostgreSQL TIMESTAMP WITH TIME ZONE.
    created_at_type = columns["created_at"]["type"]
    assert getattr(created_at_type, "timezone", False) is True

    primary_key = inspector.get_pk_constraint("favorites")
    assert primary_key["name"] == "pk_favorites"
    assert primary_key["constrained_columns"] == ["id"]

    indexes = {
        index["name"]: index
        for index in inspector.get_indexes("favorites")
    }

    # PostgreSQL may also expose the index backing the UNIQUE constraint through
    # get_indexes(), so only the two explicitly created indexes are required here.
    assert {
        "ix_favorites_destination_id",
        "ix_favorites_user_created_at",
    }.issubset(indexes)

    assert indexes["ix_favorites_destination_id"]["column_names"] == [
        "destination_id"
    ]

    assert indexes["ix_favorites_user_created_at"]["column_names"] == [
        "user_id",
        "created_at",
    ]

    unique_constraints = {
        constraint["name"]: constraint
        for constraint in inspector.get_unique_constraints("favorites")
    }

    assert "uq_favorites_user_destination" in unique_constraints
    assert unique_constraints[
        "uq_favorites_user_destination"
    ]["column_names"] == [
        "user_id",
        "destination_id",
    ]

    foreign_keys = {
        foreign_key["constrained_columns"][0]: foreign_key
        for foreign_key in inspector.get_foreign_keys("favorites")
    }

    assert set(foreign_keys) == {"user_id", "destination_id"}

    user_foreign_key = foreign_keys["user_id"]
    assert user_foreign_key["name"] == "fk_favorites_user_id_users"
    assert user_foreign_key["referred_table"] == "users"
    assert user_foreign_key["referred_columns"] == ["id"]
    assert user_foreign_key["options"].get("ondelete") == "CASCADE"

    destination_foreign_key = foreign_keys["destination_id"]
    assert (
        destination_foreign_key["name"]
        == "fk_favorites_destination_id_destinations"
    )
    assert destination_foreign_key["referred_table"] == "destinations"
    assert destination_foreign_key["referred_columns"] == ["id"]
    assert destination_foreign_key["options"].get("ondelete") == "CASCADE"


def _assert_unique_constraint_and_cascades(engine: Engine) -> None:
    """
    Verify the unique user/destination pair and both ON DELETE CASCADE rules.
    """
    with engine.begin() as connection:
        user_id = connection.scalar(
            text(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    username,
                    hashed_password
                )
                VALUES (
                    'Favorite Migration Test',
                    'favorite-migration-test@example.com',
                    'favorite-migration-test',
                    'test-hash'
                )
                RETURNING id
                """
            )
        )

        destination_id = connection.scalar(
            text(
                """
                INSERT INTO destinations (slug, status)
                VALUES (
                    'favorite-migration-test-destination',
                    'published'
                )
                RETURNING id
                """
            )
        )

        assert user_id is not None
        assert destination_id is not None

        connection.execute(
            text(
                """
                INSERT INTO favorites (user_id, destination_id)
                VALUES (:user_id, :destination_id)
                """
            ),
            {
                "user_id": user_id,
                "destination_id": destination_id,
            },
        )

        # The same user/destination pair must not be inserted twice.
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(
                    text(
                        """
                        INSERT INTO favorites (user_id, destination_id)
                        VALUES (:user_id, :destination_id)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "destination_id": destination_id,
                    },
                )

        favorite_count = connection.scalar(
            text(
                """
                SELECT count(*)
                FROM favorites
                WHERE user_id = :user_id
                  AND destination_id = :destination_id
                """
            ),
            {
                "user_id": user_id,
                "destination_id": destination_id,
            },
        )

        assert favorite_count == 1

        # Deleting the user must cascade-delete the favorite.
        connection.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )

        favorite_count_after_user_delete = connection.scalar(
            text(
                """
                SELECT count(*)
                FROM favorites
                WHERE destination_id = :destination_id
                """
            ),
            {"destination_id": destination_id},
        )

        assert favorite_count_after_user_delete == 0

        second_user_id = connection.scalar(
            text(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    username,
                    hashed_password
                )
                VALUES (
                    'Favorite Migration Test 2',
                    'favorite-migration-test-2@example.com',
                    'favorite-migration-test-2',
                    'test-hash'
                )
                RETURNING id
                """
            )
        )

        assert second_user_id is not None

        connection.execute(
            text(
                """
                INSERT INTO favorites (user_id, destination_id)
                VALUES (:user_id, :destination_id)
                """
            ),
            {
                "user_id": second_user_id,
                "destination_id": destination_id,
            },
        )

        # Deleting the destination must cascade-delete the favorite.
        connection.execute(
            text(
                """
                DELETE FROM destinations
                WHERE id = :destination_id
                """
            ),
            {"destination_id": destination_id},
        )

        favorite_count_after_destination_delete = connection.scalar(
            text(
                """
                SELECT count(*)
                FROM favorites
                WHERE user_id = :user_id
                """
            ),
            {"user_id": second_user_id},
        )

        assert favorite_count_after_destination_delete == 0

        connection.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": second_user_id},
        )


def test_favorite_migration_upgrade_downgrade_and_constraints() -> None:
    """
    Run a complete live migration lifecycle:

    clean database -> upgrade head -> inspect and test schema ->
    downgrade previous revision -> verify removal -> upgrade head again.
    """
    database_url = _test_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        # Bring the isolated database to the latest migration.
        _alembic(database_url, "upgrade", "head")

        _assert_favorites_schema(engine)
        _assert_unique_constraint_and_cascades(engine)

        # Downgrade only the Favorites migration.
        _alembic(database_url, "downgrade", PREVIOUS_REVISION)

        downgraded_inspector = inspect(engine)
        assert "favorites" not in downgraded_inspector.get_table_names()

        # Ensure the previous revision is the active revision after downgrade.
        with engine.connect() as connection:
            current_revision = connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )

        assert current_revision == PREVIOUS_REVISION

        # Reapply the migration and verify that it can be recreated cleanly.
        _alembic(database_url, "upgrade", "head")

        _assert_favorites_schema(engine)

        with engine.connect() as connection:
            current_revision = connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )

        assert current_revision == FAVORITES_REVISION

    finally:
        engine.dispose()