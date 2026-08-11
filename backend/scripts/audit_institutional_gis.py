from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from scripts.canonical_gis_review import build_canonical_review
from scripts.destination_import import load_dataset
from scripts.gis_registry import (
    audit_sources,
    build_candidates,
    canonical_destinations,
    load_manifest,
    natural_relationship,
    normalize_name,
    source_registry_entry,
    taxonomy_crosswalk,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = BACKEND_ROOT / "data" / "gis" / "source-manifest.json"
DEFAULT_DATASET = BACKEND_ROOT / "data" / "dev" / "destinations.json"
DEFAULT_OUTPUT = BACKEND_ROOT / "data" / "gis"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely audit institutional KML/GeoJSON and build review candidates.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write-reports", action="store_true", help="Atomically write registry, audit, and candidate JSON reports.")
    return parser.parse_args(argv)


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(encoded); temporary.flush(); os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try: os.unlink(temporary_name)
        except FileNotFoundError: pass
        raise


def _cross_source_duplicates(features: list[Any]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, float, float], list[Any]] = {}
    for item in features:
        if item.raw_name and item.latitude is not None and item.longitude is not None:
            groups.setdefault((normalize_name(item.raw_name), item.longitude, item.latitude), []).append(item)
    return [
        {
            "normalized_name": key[0], "longitude": key[1], "latitude": key[2],
            "features": [{"source_id": item.source_id, "feature_id": item.feature_id} for item in group],
        }
        for key, group in groups.items() if len({item.source_id for item in group}) > 1
    ]


def _malformed_context(source_dir: Path, audits: list[Any]) -> list[dict[str, Any]]:
    findings = []
    for audit in audits:
        if audit.parse_status != "malformed":
            continue
        warning = audit.warnings[0] if audit.warnings else "parse failure"
        match = __import__("re").search(r"line (\d+), column (\d+)", warning)
        excerpt = None
        if match:
            line_number = int(match.group(1))
            lines = (source_dir / audit.file_name).read_text(encoding="utf-8").splitlines()
            if 1 <= line_number <= len(lines):
                excerpt = lines[line_number - 1][:500]
        findings.append({"source_id": audit.source_id, "file_name": audit.file_name, "error": warning, "excerpt": excerpt})
    return findings


def build_reports(source_dir: Path, manifest_path: Path, dataset_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = load_manifest(manifest_path)
    dataset, dataset_hash = load_dataset(dataset_path)
    feature_sets, audits = audit_sources(manifest, source_dir)
    specs = {item.source_id: item for item in manifest.sources}
    audit_by_id = {item.source_id: item for item in audits}
    registry = {
        "schema_version": 1,
        "organization": manifest.organization,
        "sources": [source_registry_entry(spec, audit_by_id[spec.source_id], manifest.organization) for spec in manifest.sources],
    }
    natural = natural_relationship(feature_sets.get("natural-atlas-base"), feature_sets.get("natural-atlas-media"))
    if natural["status"] == "PROVEN_SAME_NATIVE_IDS":
        base_by_id = {item.source_feature_id: item for item in feature_sets["natural-atlas-base"]}
        for item in feature_sets["natural-atlas-media"]:
            base = base_by_id[item.source_feature_id]
            item.related_sources.append(f"{base.source_id}:{base.source_feature_id}")
        analysis_sets = {
            key: value for key, value in feature_sets.items() if key != "natural-atlas-base"
        }
    else:
        analysis_sets = feature_sets
    all_features = [feature for source_features in analysis_sets.values() for feature in source_features]
    canonical = canonical_destinations(dataset)
    candidates, unresolved = build_candidates(canonical, all_features, specs)
    candidate_report = {
        "schema_version": 1, "generation_policy": "exact normalized equality discovery only; human review required",
        "canonical_dataset_sha256": dataset_hash, "records": candidates, "unresolved": unresolved,
    }
    natural_features = analysis_sets.get("natural-atlas-media") or analysis_sets.get("natural-atlas-base") or []
    categories = Counter(item.category for item in natural_features if item.category)
    media_values = [value for item in all_features for value in item.media]
    audit_report = {
        "schema_version": 1,
        "summary": {
            "sources_expected": len(manifest.sources), "sources_parsed": sum(item.parse_status == "parsed" for item in audits),
            "sources_missing": sum(item.parse_status == "missing" for item in audits),
            "sources_malformed": sum(item.parse_status == "malformed" for item in audits),
            "features_normalized": len(all_features), "canonical_destinations": len(canonical),
            "exact_id_candidates": sum(item["review_status"] == "EXACT_ID" for item in candidates),
            "review_candidates": sum(item["review_status"].startswith("REVIEW_REQUIRED") for item in candidates),
            "ambiguous_candidates": sum(item["review_status"] == "AMBIGUOUS" for item in candidates),
            "unresolved_destinations": len(unresolved), "database_changes": "NONE",
        },
        "sources": [asdict(item) for item in audits],
        "natural_atlas_relationship": natural,
        "natural_atlas_statistics": {
            "status": "unavailable" if natural["status"] == "UNRESOLVED_MISSING_SOURCE" else "derived",
            "features_by_category": dict(sorted(categories.items())),
            "features_with_media": sum(bool(item.media) for item in all_features if item.source_id.startswith("natural-atlas")),
        },
        "media_metadata": {
            "features_with_media": sum(bool(item.media) for item in all_features),
            "media_references": len(media_values),
            "remote_url_references": sum(value.strip().lower().startswith(("http://", "https://")) for value in media_values),
            "local_or_embedded_references": sum(not value.strip().lower().startswith(("http://", "https://")) for value in media_values),
            "provenance_complete": 0,
            "database_import_suitable": False,
        },
        "cross_source_duplicate_name_coordinates": _cross_source_duplicates(all_features),
        "canonical_destinations": canonical,
        "taxonomy_crosswalk": taxonomy_crosswalk(all_features, canonical),
        "malformed_source_findings": _malformed_context(source_dir, audits),
    }
    canonical_review = build_canonical_review(canonical, all_features, specs, audit_by_id)
    canonical_review["malformed_source_findings"] = audit_report["malformed_source_findings"]
    return registry, candidate_report, audit_report, canonical_review


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        registry, candidates, audit, canonical_review = build_reports(args.source_dir, args.manifest, args.dataset)
    except (OSError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        print(f"GIS audit failed: {exc}", file=sys.stderr); return 2
    summary = audit["summary"]
    print(f"Sources expected: {summary['sources_expected']}")
    print(f"Sources parsed: {summary['sources_parsed']}")
    print(f"Sources missing: {summary['sources_missing']}")
    print(f"Sources malformed: {summary['sources_malformed']}")
    print(f"Features normalized: {summary['features_normalized']}")
    print(f"Canonical destinations: {summary['canonical_destinations']}")
    print(f"Exact ID candidates: {summary['exact_id_candidates']}")
    print(f"Review candidates: {summary['review_candidates']}")
    print(f"Ambiguous candidates: {summary['ambiguous_candidates']}")
    print(f"Unresolved destinations: {summary['unresolved_destinations']}")
    if args.write_reports:
        _atomic_json(args.output_dir / "institutional-sources.json", registry)
        _atomic_json(args.output_dir / "destination-source-candidates.json", candidates)
        _atomic_json(args.output_dir / "institutional-gis-audit.json", audit)
        _atomic_json(args.output_dir / "canonical-destination-coordinate-review.json", canonical_review)
        print(f"Reports written: {args.output_dir.resolve()}")
    else:
        print("Generated report changes: NONE (preview)")
    print("Database changes: NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
