# Backend database migrations

PostgreSQL with PostGIS is required for production. SQLite tests do not prove PostgreSQL/PostGIS behavior. The initial Alembic migration enables PostGIS and creates SRID 4326 point geometry with a GiST index. Confirm the migration identity may enable the extension, or have the provider enable it first.

Migrations are a separate deployment job. Web workers never run `alembic upgrade`, `create_all`, or downgrade. The sequence is linear from `24ed546b1ce8`; obtain the authoritative current head with `alembic heads` rather than copying a revision into deployment automation. Repository CI requires exactly one head and upgrades a clean PostgreSQL/PostGIS 16 database through the full chain.

## Procedure

1. Verify the target and approved backup; do not print `DATABASE_URL`.
2. Run `python -m scripts.wait_for_database` and `python -m scripts.check_database`.
3. Review `alembic history` and the exact pending migration code.
4. Run `alembic upgrade head` from one migration job.
5. Run `python -m scripts.check_migrations` and verify readiness.

The helpers are read-only except `alembic upgrade head`, exit non-zero on failure, and do not display connection values. Readiness returns 503 when connectivity, PostGIS, or the Alembic revision is not ready.

Downgrades are never automatic. Prefer a forward fix. Any downgrade requires a stopped writer fleet, current backup, explicit review/approval, and post-action data validation. Destructive migrations require a verified backup before execution.
