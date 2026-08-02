"""Bounded, non-destructive database startup wait helper."""
import time
def main(attempts: int = 12, delay_seconds: float = 2.0) -> int:
    try:
        from app.db.health import check_database_connection
    except Exception:
        print("Database configuration is invalid.")
        return 1
    for _ in range(attempts):
        if check_database_connection():
            print("Database is reachable.")
            return 0
        time.sleep(delay_seconds)
    print("Database did not become reachable before the deadline.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
