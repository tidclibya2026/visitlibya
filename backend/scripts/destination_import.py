from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.schemas.category import CategoryCreate
from app.schemas.destination import DestinationCreate, DestinationTranslationCreate
from app.services.destination import DestinationService

SUPPORTED_LOCALES = {"ar", "en"}
MAX_DATASET_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 100


class ImportCategory(CategoryCreate):
    model_config = ConfigDict(extra="forbid")


class ImportTranslation(DestinationTranslationCreate):
    model_config = ConfigDict(extra="forbid")


class ImportDestination(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    category: str
    status: DestinationStatus
    is_active: bool
    is_featured: bool = False
    priority_order: int = Field(default=0, ge=0)
    municipality: str | None = Field(default=None, max_length=150)
    region: str | None = Field(default=None, max_length=150)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    translations: list[ImportTranslation] = Field(min_length=1)

    @field_validator("latitude", "longitude")
    @classmethod
    def finite_coordinate(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("coordinates must be finite")
        return value

    @model_validator(mode="after")
    def validate_semantics(self) -> "ImportDestination":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        locales = [item.language_code for item in self.translations]
        if len(locales) != len(set(locales)):
            raise ValueError("translation locales must be unique per destination")
        unsupported = set(locales) - SUPPORTED_LOCALES
        if unsupported:
            raise ValueError(f"unsupported translation locale(s): {', '.join(sorted(unsupported))}")
        # Reuse the application's authoritative destination validation.
        DestinationCreate(
            slug=self.slug,
            category_id=None,
            status=self.status,
            latitude=self.latitude,
            longitude=self.longitude,
            municipality=self.municipality,
            region=self.region,
            priority_order=self.priority_order,
            is_featured=self.is_featured,
            is_active=self.is_active,
            translations=self.translations,
        )
        return self


class ImportDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    dataset: str = Field(min_length=1, max_length=200)
    categories: list[ImportCategory]
    records: list[ImportDestination] = Field(min_length=1, max_length=MAX_RECORDS)

    @model_validator(mode="after")
    def validate_identities(self) -> "ImportDataset":
        category_codes = [item.code for item in self.categories]
        if len(category_codes) != len(set(category_codes)):
            raise ValueError("category codes must be unique")
        slugs = [item.slug for item in self.records]
        if len(slugs) != len(set(slugs)):
            raise ValueError("destination slugs must be unique")
        missing = sorted({item.category for item in self.records} - set(category_codes))
        if missing:
            raise ValueError(f"unknown category reference(s): {', '.join(missing)}")
        return self


@dataclass
class ImportPlan:
    create_categories: list[ImportCategory] = field(default_factory=list)
    unchanged_categories: list[str] = field(default_factory=list)
    create_destinations: list[ImportDestination] = field(default_factory=list)
    unchanged_destinations: list[str] = field(default_factory=list)
    conflicts: dict[str, list[str]] = field(default_factory=dict)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def load_dataset(path: Path) -> tuple[ImportDataset, str]:
    resolved = path.resolve(strict=True)
    size = resolved.stat().st_size
    if size > MAX_DATASET_BYTES:
        raise ValueError(f"dataset exceeds {MAX_DATASET_BYTES} bytes")
    raw = resolved.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("dataset must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"dataset is not valid JSON: {exc.msg}") from exc
    return ImportDataset.model_validate(payload), hashlib.sha256(raw).hexdigest()


def _category_differences(source: ImportCategory, current: Category) -> list[str]:
    fields = ("name_ar", "name_en", "description_ar", "description_en", "icon", "is_active")
    return [name for name in fields if getattr(current, name) != getattr(source, name)]


def _translation_values(item: object) -> dict[str, object]:
    fields = (
        "name", "short_description", "description", "historical_background",
        "visitor_information", "accessibility_information", "seo_title", "seo_description",
    )
    return {name: getattr(item, name) for name in fields}


def _destination_differences(source: ImportDestination, current: Destination) -> list[str]:
    differences: list[str] = []
    current_category = current.category.code if current.category else None
    if current_category != source.category:
        differences.append("category")
    for name in (
        "status", "is_active", "is_featured", "priority_order", "municipality",
        "region", "latitude", "longitude",
    ):
        if getattr(current, name) != getattr(source, name):
            differences.append(name)
    existing = {item.language_code: item for item in current.translations}
    incoming = {item.language_code: item for item in source.translations}
    if set(existing) != set(incoming):
        differences.append("translations.locales")
    for locale in sorted(set(existing) & set(incoming)):
        if _translation_values(existing[locale]) != _translation_values(incoming[locale]):
            differences.append(f"translations.{locale}")
    return differences


def build_plan(
    dataset: ImportDataset,
    existing_categories: dict[str, Category],
    existing_destinations: dict[str, Destination],
) -> ImportPlan:
    plan = ImportPlan()
    for source in dataset.categories:
        current = existing_categories.get(source.code)
        if current is None:
            plan.create_categories.append(source)
        else:
            differences = _category_differences(source, current)
            if differences:
                plan.conflicts[f"category:{source.code}"] = differences
            else:
                plan.unchanged_categories.append(source.code)
    for source in dataset.records:
        current = existing_destinations.get(source.slug)
        if current is None:
            if f"category:{source.category}" not in plan.conflicts:
                plan.create_destinations.append(source)
        else:
            differences = _destination_differences(source, current)
            if differences:
                plan.conflicts[source.slug] = differences
            else:
                plan.unchanged_destinations.append(source.slug)
    return plan


def read_existing(session: Session, dataset: ImportDataset) -> tuple[dict[str, Category], dict[str, Destination]]:
    codes = [item.code for item in dataset.categories]
    slugs = [item.slug for item in dataset.records]
    categories = session.scalars(select(Category).where(Category.code.in_(codes))).all()
    destinations = session.scalars(
        select(Destination)
        .options(selectinload(Destination.translations))
        .where(Destination.slug.in_(slugs))
    ).all()
    return ({item.code: item for item in categories}, {item.slug: item for item in destinations})


def apply_plan(session: Session, plan: ImportPlan, existing_categories: dict[str, Category]) -> None:
    if plan.has_conflicts:
        raise ValueError("apply refused because the plan contains conflicts")
    try:
        categories = dict(existing_categories)
        for payload in plan.create_categories:
            category = Category(**payload.model_dump())
            session.add(category)
            categories[payload.code] = category
        session.flush()
        for payload in plan.create_destinations:
            values = payload.model_dump(exclude={"category", "translations"})
            destination = Destination(**values, category=categories[payload.category])
            destination.translations = [
                DestinationTranslation(**item.model_dump()) for item in payload.translations
            ]
            DestinationService._apply_coordinates(destination)
            session.add(destination)
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise


def environment_allows_apply(environment: str) -> bool:
    return environment in {"development", "test"}


def published_active_count(session: Session) -> int:
    return session.scalar(
        select(func.count(Destination.id)).where(
            Destination.status == DestinationStatus.PUBLISHED,
            Destination.is_active.is_(True),
        )
    ) or 0


def format_report(dataset: ImportDataset, digest: str, plan: ImportPlan, environment: str, apply: bool) -> str:
    complete_coordinates = sum(item.latitude is not None for item in dataset.records)
    mode = "APPLY" if apply else "DRY RUN"
    lines = [
        f"Dataset: {dataset.dataset} v{dataset.schema_version}",
        f"Dataset SHA-256: {digest}",
        f"Environment: {environment}",
        f"Mode: {mode}",
        f"Validated records: {len(dataset.records)}",
        "Plan:",
        f"  Create destinations: {len(plan.create_destinations)}",
        f"  Existing unchanged: {len(plan.unchanged_destinations)}",
        f"  Conflicts: {len(plan.conflicts)}",
        "Categories:",
        f"  Create: {len(plan.create_categories)}",
        f"  Existing unchanged: {len(plan.unchanged_categories)}",
        "Coordinates:",
        f"  Complete: {complete_coordinates}",
        f"  Missing: {len(dataset.records) - complete_coordinates}",
    ]
    for identity, fields in sorted(plan.conflicts.items()):
        lines.append(f"  Conflict {identity}: {', '.join(fields)} (no write)")
    lines.append("Database changes: PENDING EXPLICIT APPLY" if apply else "Database changes: NONE (dry run)")
    return "\n".join(lines)
