from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.session import SessionLocal
from scripts.destination_import import (
    apply_plan,
    build_plan,
    environment_allows_apply,
    format_report,
    load_dataset,
    published_active_count,
    read_existing,
)

DEFAULT_DATASET = Path(__file__).resolve().parents[1] / "data" / "dev" / "destinations.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and plan development destination fixtures.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--apply", action="store_true", help="Apply the validated, conflict-free plan.")
    return parser.parse_args(argv)


def safe_database_label() -> str:
    url = make_url(settings.database_url)
    return f"{url.host or 'local'} / {url.database or '(unnamed)'}"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        dataset, digest = load_dataset(args.dataset)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Dataset validation failed: {exc}", file=sys.stderr)
        return 2
    if args.apply and not environment_allows_apply(settings.app_env):
        print(f"Apply refused for environment: {settings.app_env}", file=sys.stderr)
        return 3
    print(f"Target database: {safe_database_label()}")
    with SessionLocal() as session:
        try:
            categories, destinations = read_existing(session, dataset)
            plan = build_plan(dataset, categories, destinations)
            print(format_report(dataset, digest, plan, settings.app_env, args.apply))
            if args.apply:
                if plan.has_conflicts:
                    print("Apply refused: resolve reported conflicts first.", file=sys.stderr)
                    return 4
                before = published_active_count(session)
                apply_plan(session, plan, categories)
                after = published_active_count(session)
                print(f"Created: {len(plan.create_destinations)}")
                print("Updated: 0")
                print(f"Unchanged: {len(plan.unchanged_destinations)}")
                print("Skipped: 0")
                print("Conflicts: 0")
                print("Failed: 0")
                print(f"Published active before: {before}")
                print(f"Published active after: {after}")
                print("Apply completed in one transaction; verify the public API before claiming publication.")
            else:
                session.rollback()
        except Exception as exc:
            session.rollback()
            print(f"Import failed: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
