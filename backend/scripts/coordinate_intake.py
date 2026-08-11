from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scripts.destination_import import ImportDataset, load_dataset

MAX_COORDINATE_FILE_BYTES = 512 * 1024


class ReviewedCoordinate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=2, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    source_reference: str = Field(min_length=1, max_length=500)
    status: Literal["reviewed"]

    @field_validator("latitude", "longitude")
    @classmethod
    def finite_coordinate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("coordinates must be finite")
        return value

    @field_validator("source_reference")
    @classmethod
    def local_source_reference(cls, value: str) -> str:
        normalized = value.strip()
        if "://" in normalized or normalized.startswith(("javascript:", "data:")):
            raise ValueError("source_reference must identify a supplied local or institutional source, not a URL")
        return normalized


class ReviewedCoordinateDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    source: str | None = Field(default=None, min_length=1, max_length=500)
    reviewed_by: str | None = Field(default=None, min_length=1, max_length=250)
    review_date: date | None = None
    records: list[ReviewedCoordinate] = Field(max_length=100)

    @field_validator("source")
    @classmethod
    def local_source(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if "://" in normalized or normalized.startswith(("javascript:", "data:")):
            raise ValueError("source must identify a supplied local or institutional source, not a URL")
        return normalized

    @model_validator(mode="after")
    def validate_review(self) -> "ReviewedCoordinateDataset":
        slugs = [item.slug for item in self.records]
        if len(slugs) != len(set(slugs)):
            raise ValueError("reviewed coordinate slugs must be unique")
        if self.records and self.source is None:
            raise ValueError("source is required when coordinate records are present")
        return self


@dataclass
class CoordinateMergePlan:
    merged_dataset: ImportDataset
    ready: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: dict[str, str] = field(default_factory=dict)
    blocked: dict[str, str] = field(default_factory=dict)

    @property
    def can_write(self) -> bool:
        return not self.conflicts and not self.blocked


def load_reviewed_coordinates(path: Path) -> tuple[ReviewedCoordinateDataset, str]:
    resolved = path.resolve(strict=True)
    if resolved.stat().st_size > MAX_COORDINATE_FILE_BYTES:
        raise ValueError(f"coordinate intake exceeds {MAX_COORDINATE_FILE_BYTES} bytes")
    raw = resolved.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("coordinate intake must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"coordinate intake is not valid JSON: {exc.msg}") from exc
    return ReviewedCoordinateDataset.model_validate(payload), hashlib.sha256(raw).hexdigest()


def build_coordinate_merge(
    canonical: ImportDataset,
    reviewed: ReviewedCoordinateDataset,
) -> CoordinateMergePlan:
    payload = canonical.model_dump(mode="json")
    merged = ImportDataset.model_validate(payload)
    records = {item.slug: item for item in merged.records}
    plan = CoordinateMergePlan(merged_dataset=merged)
    for item in reviewed.records:
        destination = records.get(item.slug)
        if destination is None:
            plan.blocked[item.slug] = "slug is not present in the canonical destination dataset"
            continue
        current = (destination.latitude, destination.longitude)
        incoming = (item.latitude, item.longitude)
        if current == (None, None):
            destination.latitude, destination.longitude = incoming
            plan.ready.append(item.slug)
        elif current == incoming:
            plan.unchanged.append(item.slug)
        else:
            plan.conflicts[item.slug] = "canonical dataset already contains a different coordinate pair"
    # Re-validate the fully merged application dataset before it can be written.
    plan.merged_dataset = ImportDataset.model_validate(plan.merged_dataset.model_dump(mode="json"))
    return plan


def write_dataset_atomic(path: Path, dataset: ImportDataset) -> tuple[str, str]:
    target = path.resolve(strict=True)
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    encoded = (json.dumps(dataset.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    after = hashlib.sha256(encoded).hexdigest()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return before, after


def coordinate_coverage(dataset: ImportDataset) -> tuple[int, int]:
    complete = sum(item.latitude is not None and item.longitude is not None for item in dataset.records)
    return complete, len(dataset.records) - complete
