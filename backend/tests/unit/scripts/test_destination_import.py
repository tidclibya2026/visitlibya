import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.models.category import Category
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from scripts.destination_import import (
    ImportDataset,
    apply_plan,
    build_plan,
    environment_allows_apply,
    load_dataset,
)


def payload() -> dict:
    return {
        "schema_version": 1,
        "dataset": "test-development-destinations",
        "categories": [
            {"code": "archaeological-sites", "name_ar": "المواقع الأثرية", "name_en": "Archaeological Sites"}
        ],
        "records": [
            {
                "slug": "leptis-magna",
                "category": "archaeological-sites",
                "status": "published",
                "is_active": True,
                "latitude": 32.64,
                "longitude": 14.29,
                "translations": [
                    {"language_code": "en", "name": "Leptis Magna"},
                    {"language_code": "ar", "name": "لبدة الكبرى"},
                ],
            }
        ],
    }


def model() -> ImportDataset:
    return ImportDataset.model_validate(payload())


def current_records(dataset: ImportDataset) -> tuple[Category, Destination]:
    source_category = dataset.categories[0]
    category = Category(id=1, **source_category.model_dump())
    source = dataset.records[0]
    destination = Destination(
        id=1,
        slug=source.slug,
        category=category,
        status=source.status,
        is_active=source.is_active,
        is_featured=source.is_featured,
        priority_order=source.priority_order,
        municipality=source.municipality,
        region=source.region,
        latitude=source.latitude,
        longitude=source.longitude,
    )
    destination.translations = [DestinationTranslation(**item.model_dump()) for item in source.translations]
    return category, destination


def test_valid_dataset() -> None:
    assert model().records[0].translations[1].name == "لبدة الكبرى"


def test_invalid_schema_version() -> None:
    data = payload(); data["schema_version"] = 2
    with pytest.raises(ValidationError): ImportDataset.model_validate(data)


def test_duplicate_slug() -> None:
    data = payload(); data["records"].append(dict(data["records"][0]))
    with pytest.raises(ValidationError, match="slugs must be unique"): ImportDataset.model_validate(data)


def test_invalid_slug() -> None:
    data = payload(); data["records"][0]["slug"] = "Not Valid"
    with pytest.raises(ValidationError): ImportDataset.model_validate(data)


def test_duplicate_locale() -> None:
    data = payload(); data["records"][0]["translations"][1]["language_code"] = "en"
    with pytest.raises(ValidationError, match="locales must be unique"): ImportDataset.model_validate(data)


@pytest.mark.parametrize("latitude,longitude", [(32.6, None), (None, 14.2)])
def test_partial_coordinates(latitude, longitude) -> None:
    data = payload(); data["records"][0]["latitude"] = latitude; data["records"][0]["longitude"] = longitude
    with pytest.raises(ValidationError, match="provided together"): ImportDataset.model_validate(data)


@pytest.mark.parametrize("field,value", [("latitude", 91), ("longitude", -181)])
def test_out_of_range_coordinates(field, value) -> None:
    data = payload(); data["records"][0][field] = value
    with pytest.raises(ValidationError): ImportDataset.model_validate(data)


def test_media_input_is_rejected_in_v1() -> None:
    data = payload(); data["records"][0]["media"] = [{"file_path": "../../private.jpg"}]
    with pytest.raises(ValidationError, match="media"): ImportDataset.model_validate(data)


def test_existing_identical_record_is_unchanged() -> None:
    dataset = model(); category, destination = current_records(dataset)
    plan = build_plan(dataset, {category.code: category}, {destination.slug: destination})
    assert plan.unchanged_destinations == ["leptis-magna"]
    assert not plan.create_destinations and not plan.conflicts


def test_conflict_does_not_plan_overwrite() -> None:
    dataset = model(); category, destination = current_records(dataset); destination.region = "Different"
    plan = build_plan(dataset, {category.code: category}, {destination.slug: destination})
    assert plan.conflicts["leptis-magna"] == ["region"]
    assert not plan.create_destinations


def test_repeated_plan_is_idempotent() -> None:
    dataset = model(); first = build_plan(dataset, {}, {})
    assert len(first.create_destinations) == 1
    category, destination = current_records(dataset)
    second = build_plan(dataset, {category.code: category}, {destination.slug: destination})
    assert len(second.unchanged_destinations) == 1
    assert not second.create_destinations


def test_apply_environment_gate() -> None:
    assert environment_allows_apply("development")
    assert environment_allows_apply("test")
    assert not environment_allows_apply("staging")
    assert not environment_allows_apply("production")


class FakeSession:
    def __init__(self, fail_flush: bool = False):
        self.added = []; self.commits = 0; self.rollbacks = 0; self.flushes = 0; self.fail_flush = fail_flush
    def add(self, value): self.added.append(value)
    def flush(self):
        self.flushes += 1
        if self.fail_flush: raise RuntimeError("database error")
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def test_dry_run_plan_performs_zero_commits() -> None:
    session = FakeSession()
    plan = build_plan(model(), {}, {})
    assert plan.create_destinations and session.commits == 0 and not session.added


def test_apply_uses_one_commit() -> None:
    dataset = model(); plan = build_plan(dataset, {}, {}); session = FakeSession()
    apply_plan(session, plan, {})
    assert session.commits == 1 and session.rollbacks == 0


def test_transaction_rolls_back_on_error() -> None:
    dataset = model(); plan = build_plan(dataset, {}, {}); session = FakeSession(fail_flush=True)
    with pytest.raises(RuntimeError, match="database error"): apply_plan(session, plan, {})
    assert session.commits == 0 and session.rollbacks == 1


def test_load_dataset_hashes_utf8(tmp_path: Path) -> None:
    path = tmp_path / "destinations.json"
    path.write_text(json.dumps(payload(), ensure_ascii=False), encoding="utf-8")
    dataset, digest = load_dataset(path)
    assert dataset.records[0].translations[1].name == "لبدة الكبرى"
    assert len(digest) == 64
