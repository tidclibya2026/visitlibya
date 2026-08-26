import json
from pathlib import Path

import pytest

from app.planner.execution import (
    estimated_travel_minutes,
    insert_meal_rest,
    normalize_destination,
    optimize,
    road_profile,
    schedule_destinations,
    visit_duration_minutes,
    execute_planner,
)


FIXTURES = Path(__file__).parents[2] / "fixtures"


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", load("planner_parity_inputs.json"), ids=lambda item: item["id"])
def test_python_core_matches_javascript_golden_fixture(case):
    expected = load("planner_parity_expected.json")[case["id"]]
    if "authority" in case:
        normalized = normalize_destination(case["authority"])
        actual = {"slug": normalized["slug"], "visitMinutes": visit_duration_minutes(normalized, case["pace"]), "opening": [normalized.get("opening_time"), normalized.get("closing_time")], "authority": normalized["planner_authority"]}
    elif "optimization" in case:
        result = optimize(case["optimization"]["days"])
        actual = {"actions": result["actions"], "summary": result["summary"], "optimizedSlugs": [item["slug"] for item in result["optimizedDays"][0]["destinations"]]}
    else:
        scheduled = schedule_destinations(case["destinations"], case["pace"])
        actual = {
            "visits": [{key: item[key] if key != "slug" else item["destination"]["slug"] for key in ("slug", "scheduled", "reason", "startsAt", "endsAt", "visitMinutes")} for item in scheduled],
            "breaks": [item["type"] for item in insert_meal_rest(scheduled, case["pace"]) if item.get("type") in {"meal", "rest"}],
            "travelMinutes": estimated_travel_minutes(case["destinations"][0], case["destinations"][1]) if len(case["destinations"]) > 1 else None,
            "road": [road_profile(item) | {"penalty": {"standard": 0, "regional": 3, "long-distance": 5, "remote": 10, "desert": 18, "desert-expedition": 25}.get(road_profile(item)["accessClass"], 0)} for item in case["destinations"]],
        }
    if actual.get("travelMinutes") is not None:
        assert actual.pop("travelMinutes") == pytest.approx(expected.pop("travelMinutes"), rel=1e-12)
    assert actual == expected


def test_unverified_authority_is_not_promoted_to_verified():
    case = next(item for item in load("planner_parity_inputs.json") if item["id"] == "unverified-authority")
    authority = normalize_destination(case["authority"])["planner_authority"]
    assert authority["profileState"] == "unverified"
    assert authority["verificationStatus"] == "unverified"
    assert authority["verifiedAt"] is None


def test_execute_planner_builds_requested_multi_day_result():
    destinations = [
        {"slug": f"stop-{index}", "category_key": "heritage", "planner_priority": 100 - index}
        for index in range(4)
    ]
    result = execute_planner(destinations, {"days": 2, "pace": "balanced"})
    assert result["requestedDays"] == 2
    assert result["selectedCount"] == 4
    assert [len(day["destinations"]) for day in result["days"]] == [2, 2]
    assert all("summary" in day and "timeline" in day for day in result["days"])
