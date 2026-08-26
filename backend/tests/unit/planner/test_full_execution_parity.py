import json
import subprocess
from pathlib import Path

import pytest

from app.planner.execution import execute_planner


FIXTURES = Path(__file__).parents[2] / "fixtures"
REPOSITORY = Path(__file__).parents[4]


def project(result):
    return {
        "days": [
            {
                "dayNumber": day["dayNumber"], "type": day["type"],
                "slugs": [item["slug"] for item in day["destinations"]],
                "timeline": [
                    {"type": item["type"], "slug": (item.get("destination") or {}).get("slug"), "scheduled": item.get("scheduled"), "conflictAdjusted": item.get("conflictAdjusted")}
                    for item in day.get("timeline", [])
                ],
                "summary": day.get("summary"),
            }
            for day in result["days"]
        ],
        "scores": [
            {"slug": item["slug"], "total": item["planner_score"]["total"], "interestScore": item["planner_score"]["interestScore"], "geographicPenalty": item["planner_score"]["geographicPenalty"], "routingMode": item["planner_score"]["routingMode"], "authority": item.get("planner_authority")}
            for day in result["days"] for item in day["destinations"]
        ],
        "feasibility": result["feasibility"],
        "recommendationCodes": [item["code"] for item in result["recommendations"]["recommendations"]],
        "optimization": {"actions": result["optimization"]["actions"], "summary": result["optimization"]["summary"], "improvement": result["optimization"]["improvement"], "beforeScore": result["optimization"]["before"]["feasibility"]["score"], "afterScore": result["optimization"]["after"]["feasibility"]["score"]},
        "selectedCount": result["selectedCount"],
    }


def javascript_goldens():
    completed = subprocess.run(
        ["node", str(FIXTURES / "generate_planner_full_parity.mjs")],
        cwd=REPOSITORY, check=True, capture_output=True, text=True,
    )
    return json.loads(completed.stdout)


CASES = json.loads((FIXTURES / "planner_full_parity_inputs.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda item: item["id"])
def test_full_python_execution_matches_javascript_reference(case):
    expected = javascript_goldens()[case["id"]]
    assert project(execute_planner(case["destinations"], case["preferences"])) == expected


def test_every_full_parity_case_uses_authority_shaped_inputs():
    for case in CASES:
        for destination in case["destinations"]:
            assert {"destination_id", "profile_state", "operational_data", "translations"} <= destination.keys()


def test_unverified_full_execution_state_is_preserved():
    case = next(item for item in CASES if item["id"] == "unverified-preserved")
    result = execute_planner(case["destinations"], case["preferences"])
    assert result["days"][0]["destinations"][0]["planner_authority"] == {
        "status": "backend", "profileState": "unverified",
        "verificationStatus": "unverified", "verifiedAt": None,
    }
