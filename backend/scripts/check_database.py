"""Perform non-destructive PostgreSQL and PostGIS readiness checks."""
def main() -> int:
    try:
        from app.db.health import check_database_connection, check_postgis
        connected = check_database_connection()
        spatial = connected and check_postgis()
    except Exception:
        connected = spatial = False
    if not connected:
        print("Database check failed.")
        return 1
    if not spatial:
        print("PostGIS check failed.")
        return 1
    print("Database and PostGIS checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
