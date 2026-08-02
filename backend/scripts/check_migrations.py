"""Check that the connected database is at every Alembic head."""
def main() -> int:
    try:
        from app.db.health import migration_is_current
        current = migration_is_current()
    except Exception:
        current = False
    if not current:
        print("Migration check failed: database revision is not current.")
        return 1
    print("Migration check passed: database is at the expected head.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
