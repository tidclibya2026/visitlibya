"""Deterministic Phase 2 public-artifact generation and direct-edit detection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.publication_governance import (
    BASELINE_CLASSIFICATION,
    GovernanceValidationError,
    REPOSITORY_ROOT,
    _measure_count,
    _tracked_paths,
    canonical_governed_bytes,
    validate_repository,
)

MANIFEST_PATH = Path("backend/data/governance/publication-generation-manifest.json")
LEDGER_PATH = Path("backend/data/governance/publication-approval-ledger.jsonl")
PROTECTED_OUTPUTS = (
    "assets/js/data/natural-tourism-layers.js",
    "assets/js/data/curated-destinations.js",
    "backend/data/dev/destinations.json",
)
NATURAL_OUTPUT = PROTECTED_OUTPUTS[0]
NATURAL_INPUTS = (
    "backend/data/gis/green-mountain-tourism-curated.review.json",
    "backend/data/gis/libyan-sahara-tourism-curated.review.json",
)
GENERATION_CLASSIFICATION = "LEGACY_COMPATIBILITY_GENERATION_NOT_INSTITUTIONAL_APPROVAL"
SUPPORTED_GENERATOR = "visit-libya-natural-tourism-layers-v1"
FORBIDDEN_NATURAL_IDS = {832, 913}

CATEGORY_PRESENTATION = {
    "الأودية ومصباتها": ("الأودية", "Wadis"),
    "البحيرات الطبيعية والصحراوية": ("البحيرات", "Natural & Desert Lakes"),
    "البرك والبلطات والقلتات": ("البرك والقلتات", "Pools & Gueltas"),
    "السبخات والأراضي الرطبة": ("السبخات والأراضي الرطبة", "Sabkhas & Wetlands"),
    "العيون الطبيعية": ("العيون الطبيعية", "Natural Springs"),
    "الفوارات والمياه الكبريتية والحمامات": ("المياه الكبريتية والحمامات", "Thermal & Sulphur Springs"),
    "محميات وموائل الطيور المهاجرة": ("المحميات والموائل الطبيعية", "Protected Habitats"),
}

MANIFEST_KEYS = {"schema_version", "manifest_id", "generator", "governance", "protected_outputs"}
OUTPUT_KEYS = {
    "path", "governed_inputs", "generator_identifier", "generator_version",
    "serialization_contract", "expected_record_count", "expected_sha256",
    "expected_byte_size", "governance_classification",
    "deterministic_regeneration_supported", "blocker",
}
INPUT_KEYS = {"path", "record_count", "ordered_source_ids_sha256"}
SERIALIZATION_CONTRACT = {
    "encoding": "UTF-8",
    "bom": False,
    "newline": "LF",
    "indent_spaces": 2,
    "key_order": "EXPLICIT_CONTRACT_ORDER",
    "record_order": "GOVERNED_INPUT_ORDER",
    "ensure_ascii": False,
    "terminal_newline": True,
    "javascript_wrapper": "ES_MODULE_OBJECT_FREEZE_V1",
}


class GenerationValidationError(ValueError):
    """A deterministic-generation or direct-edit invariant failed."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise GenerationValidationError(f"BOM is prohibited: {path}")
        value = json.loads(raw.decode("utf-8"))
    except GenerationValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GenerationValidationError(f"cannot read valid UTF-8 JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GenerationValidationError(f"JSON root must be an object: {path}")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise GenerationValidationError(
            f"{label} keys differ; missing={sorted(expected - set(value))}, extra={sorted(set(value) - expected)}"
        )


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ordered_ids_hash(ids: list[int]) -> str:
    return _sha256_bytes(",".join(str(value) for value in ids).encode("ascii"))


def _baseline_by_path(root: Path) -> dict[str, dict[str, Any]]:
    baseline = _load_json(root / "backend/data/governance/legacy-publication-baseline.json")
    return {item["path"]: item for item in baseline["artifacts"]}


def load_manifest(root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    return _load_json(root / MANIFEST_PATH)


def validate_manifest(
    root: Path,
    manifest: dict[str, Any],
    *,
    tracked_paths: set[str] | None = None,
) -> None:
    _exact_keys(manifest, MANIFEST_KEYS, "manifest")
    if manifest["schema_version"] != 1:
        raise GenerationValidationError("unsupported generation manifest schema_version")
    if manifest["manifest_id"] != "visit-libya-publication-generation-phase-2":
        raise GenerationValidationError("unexpected generation manifest_id")
    if manifest["generator"] != {
        "identifier": "visit-libya-publication-generation",
        "version": "1.0.0-phase-2",
        "implementation": "backend/scripts/publication_generation.py",
    }:
        raise GenerationValidationError("generator contract does not match Phase 2")
    if manifest["governance"] != {
        "classification": GENERATION_CLASSIFICATION,
        "policy": "backend/data/governance/publication-policy.json",
        "approval_ledger": "backend/data/governance/publication-approval-ledger.jsonl",
        "legacy_baseline": "backend/data/governance/legacy-publication-baseline.json",
        "empty_ledger_required": True,
        "approval_values_must_remain_false": True,
        "runtime_behavior_unchanged": True,
    }:
        raise GenerationValidationError("manifest governance contract is invalid")

    outputs = manifest["protected_outputs"]
    if not isinstance(outputs, list) or len(outputs) != 3:
        raise GenerationValidationError("manifest must contain exactly three protected outputs")
    paths = [item.get("path") for item in outputs if isinstance(item, dict)]
    if paths != list(PROTECTED_OUTPUTS) or len(paths) != len(set(paths)):
        raise GenerationValidationError("protected output path allowlist or order is invalid")
    tracked = tracked_paths if tracked_paths is not None else _tracked_paths(root)
    baseline = _baseline_by_path(root)

    for item in outputs:
        _exact_keys(item, OUTPUT_KEYS, f"output {item.get('path')}")
        path = item["path"]
        if path not in tracked or not (root / path).is_file():
            raise GenerationValidationError(f"protected output must exist and be tracked: {path}")
        base = baseline.get(path)
        if base is None:
            raise GenerationValidationError(f"protected output is absent from the Phase 1 baseline: {path}")
        for key in ("expected_sha256", "expected_byte_size", "expected_record_count"):
            baseline_key = {"expected_sha256": "sha256", "expected_byte_size": "byte_size", "expected_record_count": "record_count"}[key]
            if item[key] != base[baseline_key]:
                raise GenerationValidationError(f"manifest {key} diverges from Phase 1 baseline: {path}")
        if item["governance_classification"] != BASELINE_CLASSIFICATION:
            raise GenerationValidationError(f"protected output implies approval: {path}")

        if item["deterministic_regeneration_supported"] is True:
            if path != NATURAL_OUTPUT or item["generator_identifier"] != SUPPORTED_GENERATOR or item["generator_version"] != 1:
                raise GenerationValidationError(f"unsupported deterministic generator declaration: {path}")
            if item["serialization_contract"] != SERIALIZATION_CONTRACT or item["blocker"] is not None:
                raise GenerationValidationError("natural output serialization or blocker contract is invalid")
            inputs = item["governed_inputs"]
            if not isinstance(inputs, list) or [entry.get("path") for entry in inputs] != list(NATURAL_INPUTS):
                raise GenerationValidationError("natural governed input allowlist or order is invalid")
            for source in inputs:
                _exact_keys(source, INPUT_KEYS, f"input {source.get('path')}")
                if source["path"] not in tracked or not (root / source["path"]).is_file():
                    raise GenerationValidationError(f"governed input must exist and be tracked: {source['path']}")
                if not isinstance(source["record_count"], int) or source["record_count"] < 1:
                    raise GenerationValidationError("governed input record_count must be positive")
                if re.fullmatch(r"[0-9a-f]{64}", str(source["ordered_source_ids_sha256"])) is None:
                    raise GenerationValidationError("governed input identity digest is invalid")
        else:
            if item["governed_inputs"] != [] or item["generator_identifier"] is not None or item["generator_version"] is not None or item["serialization_contract"] is not None:
                raise GenerationValidationError(f"unsupported regeneration must not claim a generator: {path}")
            if not isinstance(item["blocker"], str) or not item["blocker"].strip():
                raise GenerationValidationError(f"frozen legacy output requires a blocker: {path}")


def _validated_source_records(root: Path, source_contract: dict[str, Any]) -> list[dict[str, Any]]:
    payload = _load_json(root / source_contract["path"])
    records = payload.get("records")
    if not isinstance(records, list):
        raise GenerationValidationError(f"governed input records are missing: {source_contract['path']}")
    ids: list[int] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not isinstance(record.get("source_feature_id"), int):
            raise GenerationValidationError(f"invalid source identity at {source_contract['path']} record {index}")
        ids.append(record["source_feature_id"])
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise GenerationValidationError(f"duplicate source IDs in {source_contract['path']}: {duplicates}")
    prohibited = sorted(FORBIDDEN_NATURAL_IDS.intersection(ids))
    if prohibited:
        raise GenerationValidationError(f"heritage-review IDs are prohibited from the natural output: {prohibited}")
    if len(records) != source_contract["record_count"]:
        raise GenerationValidationError(f"missing or unexpected source ID count in {source_contract['path']}")
    if _ordered_ids_hash(ids) != source_contract["ordered_source_ids_sha256"]:
        raise GenerationValidationError(f"missing, unexpected, or reordered source IDs in {source_contract['path']}")
    return records


def _natural_feature(record: dict[str, Any], layer: str) -> dict[str, Any]:
    required = {
        "source_feature_id", "name", "primary_category", "longitude", "latitude",
        "media_companion_found", "publication_approved", "curation_status",
    }
    missing = sorted(required - set(record))
    if missing:
        raise GenerationValidationError(f"natural source record is missing fields {missing}")
    category = record["primary_category"]
    if category not in CATEGORY_PRESENTATION:
        raise GenerationValidationError(f"unsupported natural category: {category}")
    if record["publication_approved"] is not False:
        raise GenerationValidationError(f"publication_approved must remain false for source ID {record['source_feature_id']}")
    if record["curation_status"] != "CURATED_TOURISM_CANDIDATE":
        raise GenerationValidationError(f"unexpected curation status for source ID {record['source_feature_id']}")
    category_ar, category_en = CATEGORY_PRESENTATION[category]
    return {
        "id": f"{layer}-{record['source_feature_id']}",
        "sourceFeatureId": record["source_feature_id"],
        "layer": layer,
        "nameAr": record["name"],
        "nameEn": "",
        "categoryAr": category_ar,
        "categoryEn": category_en,
        "categoryKey": category,
        "latitude": record["latitude"],
        "longitude": record["longitude"],
        "mediaAvailable": record["media_companion_found"],
        "source": record.get("source", ""),
        "origin": record.get("origin", ""),
        "reviewStatus": record["curation_status"],
        "publicationApproved": False,
    }


def _render_natural_bytes(root: Path, manifest: dict[str, Any]) -> tuple[bytes, int]:
    contract = next(item for item in manifest["protected_outputs"] if item["path"] == NATURAL_OUTPUT)
    green = _validated_source_records(root, contract["governed_inputs"][0])
    sahara = _validated_source_records(root, contract["governed_inputs"][1])
    payload = {
        "schemaVersion": 1,
        "generatedFrom": {
            "greenMountain": "green-mountain-tourism-curated.review.json",
            "libyanSahara": "libyan-sahara-tourism-curated.review.json",
        },
        "publicationPolicy": "reviewed-curated-not-independently-published",
        "layers": {
            "green-mountain": {
                "slug": "green-mountain",
                "nameAr": "الجبل الأخضر",
                "nameEn": "Jebel Akhdar",
                "featureCount": len(green),
                "features": [_natural_feature(record, "green-mountain") for record in green],
            },
            "libyan-sahara": {
                "slug": "desert",
                "nameAr": "الصحراء الليبية",
                "nameEn": "Libyan Sahara",
                "featureCount": len(sahara),
                "features": [_natural_feature(record, "libyan-sahara") for record in sahara],
            },
        },
    }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    text = (
        "// Generated from reviewed institutional GIS artifacts.\n"
        "// Do not edit feature coordinates manually.\n\n"
        "export const naturalTourismLayers = Object.freeze("
        f"{json_text});\n\n"
        "export function getNaturalTourismLayer(layerId) {\n"
        "  return naturalTourismLayers.layers[layerId] ?? null;\n"
        "}\n\n"
        "export function getNaturalTourismFeatures(layerId) {\n"
        "  return getNaturalTourismLayer(layerId)?.features ?? [];\n"
        "}\n"
    )
    raw = text.encode("utf-8")
    return raw, len(green) + len(sahara)


def generate_natural_bytes(root: Path, manifest: dict[str, Any]) -> bytes:
    contract = next(item for item in manifest["protected_outputs"] if item["path"] == NATURAL_OUTPUT)
    raw, record_count = _render_natural_bytes(root, manifest)
    if record_count != contract["expected_record_count"]:
        raise GenerationValidationError("generated natural feature count does not match manifest")
    if len(raw) != contract["expected_byte_size"] or _sha256_bytes(raw) != contract["expected_sha256"]:
        raise GenerationValidationError("generated natural bytes do not match the frozen Phase 1 output contract")
    return raw


def validate_phase_2(root: Path = REPOSITORY_ROOT, *, tracked_paths: set[str] | None = None) -> dict[str, Any]:
    try:
        validate_repository(root, tracked_paths=tracked_paths, enforce_git=False)
    except GovernanceValidationError as exc:
        raise GenerationValidationError(str(exc)) from exc
    if (root / LEDGER_PATH).read_bytes() != b"":
        raise GenerationValidationError("Phase 2 requires an empty zero-byte approval ledger")
    manifest = load_manifest(root)
    validate_manifest(root, manifest, tracked_paths=tracked_paths)
    return manifest


def verify_protected(root: Path = REPOSITORY_ROOT, *, tracked_paths: set[str] | None = None) -> dict[str, str]:
    manifest = validate_phase_2(root, tracked_paths=tracked_paths)
    results: dict[str, str] = {}
    for contract in manifest["protected_outputs"]:
        path = contract["path"]
        actual = canonical_governed_bytes(root / path)
        if len(actual) != contract["expected_byte_size"] or _sha256_bytes(actual) != contract["expected_sha256"]:
            raise GenerationValidationError(f"direct edit or protected-byte mismatch detected: {path}")
        semantics = _baseline_by_path(root)[path]["count_semantics"]
        if _measure_count(root / path, semantics) != contract["expected_record_count"]:
            raise GenerationValidationError(f"protected record-count mismatch: {path}")
        if contract["deterministic_regeneration_supported"]:
            generated = generate_natural_bytes(root, manifest)
            if generated != actual:
                raise GenerationValidationError(f"generated bytes differ from committed protected artifact: {path}")
            results[path] = "DETERMINISTIC_GENERATION_SUPPORTED_BYTE_IDENTICAL"
        else:
            results[path] = "FROZEN_LEGACY_VERIFICATION_ONLY"
    return results


def generate_to_directory(root: Path, output_dir: Path, *, tracked_paths: set[str] | None = None) -> list[Path]:
    manifest = validate_phase_2(root, tracked_paths=tracked_paths)
    output_dir = output_dir.resolve()
    root_resolved = root.resolve()
    if output_dir == root_resolved or root_resolved in output_dir.parents:
        raise GenerationValidationError("output directory must be outside the repository; use guarded replace for protected paths")
    raw = generate_natural_bytes(root, manifest)
    destination = output_dir / NATURAL_OUTPUT
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return [destination]


def replace_supported(
    root: Path,
    *,
    allow_protected_replacement: bool,
    tracked_paths: set[str] | None = None,
) -> list[Path]:
    if not allow_protected_replacement:
        raise GenerationValidationError("protected replacement requires --allow-protected-replacement")
    manifest = validate_phase_2(root, tracked_paths=tracked_paths)
    raw = generate_natural_bytes(root, manifest)
    destination = root / NATURAL_OUTPUT
    current = canonical_governed_bytes(destination)
    if current == raw:
        return []
    if _sha256_bytes(current) != next(item["expected_sha256"] for item in manifest["protected_outputs"] if item["path"] == NATURAL_OUTPUT):
        raise GenerationValidationError("refusing replacement because the protected output has an unreviewed direct edit")
    print(f"WILL REPLACE protected output: {NATURAL_OUTPUT}", file=sys.stderr)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return [destination]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-manifest", help="validate Phase 1 and the Phase 2 manifest without writes")
    sub.add_parser("verify", help="regenerate in memory and detect protected direct edits")
    generate = sub.add_parser("generate", help="generate supported outputs outside the repository")
    generate.add_argument("--output-dir", required=True, type=Path)
    replace = sub.add_parser("replace", help="explicit guarded replacement of supported protected outputs")
    replace.add_argument("--allow-protected-replacement", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate-manifest":
            validate_phase_2()
            print("PASS publication generation manifest: 1 deterministic; 2 frozen legacy; ledger empty")
        elif args.command == "verify":
            results = verify_protected()
            print("PASS protected publication artifacts: " + "; ".join(f"{path}={state}" for path, state in results.items()))
        elif args.command == "generate":
            outputs = generate_to_directory(REPOSITORY_ROOT, args.output_dir)
            print("PASS generated outside repository: " + ", ".join(str(path) for path in outputs))
        elif args.command == "replace":
            outputs = replace_supported(REPOSITORY_ROOT, allow_protected_replacement=args.allow_protected_replacement)
            if outputs:
                print("REPLACED: " + ", ".join(str(path) for path in outputs))
            else:
                print("PASS protected output already byte-identical; no replacement written")
        return 0
    except GenerationValidationError as exc:
        print(f"FAIL publication generation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
