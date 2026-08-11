from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from scripts.coordinate_intake import (
    build_coordinate_merge,
    coordinate_coverage,
    load_reviewed_coordinates,
    write_dataset_atomic,
)
from scripts.destination_import import load_dataset

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = BACKEND_ROOT / "data" / "dev" / "destinations.json"
DEFAULT_COORDINATES = BACKEND_ROOT / "data" / "dev" / "destination-coordinates.reviewed.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and preview exact-slug reviewed coordinate intake.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--coordinates", type=Path, default=DEFAULT_COORDINATES)
    parser.add_argument(
        "--write-dataset",
        action="store_true",
        help="Atomically update only the canonical JSON dataset; never writes to the database.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        canonical, canonical_hash = load_dataset(args.dataset)
        reviewed, reviewed_hash = load_reviewed_coordinates(args.coordinates)
        plan = build_coordinate_merge(canonical, reviewed)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Coordinate intake validation failed: {exc}", file=sys.stderr)
        return 2
    before_complete, before_missing = coordinate_coverage(canonical)
    after_complete, after_missing = coordinate_coverage(plan.merged_dataset)
    print(f"Canonical dataset SHA-256: {canonical_hash}")
    print(f"Reviewed intake SHA-256: {reviewed_hash}")
    print("Mode: WRITE DATASET" if args.write_dataset else "Mode: PREVIEW")
    print(f"Reviewed records: {len(reviewed.records)}")
    print(f"Ready: {len(plan.ready)}")
    print(f"Unchanged: {len(plan.unchanged)}")
    print(f"Conflicts: {len(plan.conflicts)}")
    print(f"Blocked: {len(plan.blocked)}")
    print(f"Coordinate coverage before: {before_complete} complete, {before_missing} missing")
    print(f"Coordinate coverage after: {after_complete} complete, {after_missing} missing")
    for slug, reason in sorted({**plan.conflicts, **plan.blocked}.items()):
        print(f"  {slug}: {reason}")
    if args.write_dataset:
        if not plan.can_write:
            print("Write refused: resolve conflicts and blocked identities first.", file=sys.stderr)
            return 3
        before_hash, after_hash = write_dataset_atomic(args.dataset, plan.merged_dataset)
        print(f"Dataset hash before: {before_hash}")
        print(f"Dataset hash after: {after_hash}")
        print("Canonical dataset updated atomically. Database changes: NONE")
    else:
        print("Canonical dataset changes: NONE (preview)")
        print("Database changes: NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
