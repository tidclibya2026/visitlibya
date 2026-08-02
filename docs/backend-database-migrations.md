# Backend database migrations

PostgreSQL with PostGIS is required for production. SQLite tests do not prove PostgreSQL/PostGIS behavior. The initial Alembic migration enables PostGIS and creates SRID 4326 point geometry with a GiST index. Confirm the migration identity may enable the extension, or have the provider enable it first.

Migrations are a separate deployment job. Web workers never run `alembic upgrade`, `create_all`, or downgrade. The current sequence is linear from `24ed546b1ce8` through head `f6b2c9d41a73`.

## Procedure

1. Verify the target and approved backup; do not print `DATABASE_URL`.
2. Run `python -m scripts.wait_for_database` and `python -m scripts.check_database`.
3. Review `alembic history` and the exact pending migration code.
4. Run `alembic upgrade head` from one migration job.
5. Run `python -m scripts.check_migrations` and verify readiness.

The helpers are read-only except `alembic upgrade head`, exit non-zero on failure, and do not display connection values. Readiness returns 503 while the revision differs from Alembic heads.

Downgrades are never automatic. Prefer a forward fix. Any downgrade requires a stopped writer fleet, current backup, explicit review/approval, and post-action data validation. Destructive migrations require a verified backup before execution.
