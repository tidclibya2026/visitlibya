"""Pure deterministic planner core aligned with the JavaScript reference.

This module deliberately has no FastAPI, database, network, or LLM dependency.
Callers must obtain destination authority records through
``PlannerDestinationAuthorityService`` before normalizing and executing them.
"""

from __future__ import annotations

from copy import deepcopy
from math import asin, cos, radians, sin, sqrt
from typing import Any, Iterable, Mapping, Sequence, TypedDict


class PlannerPreferences(TypedDict, total=False):
    days: int
    pace: str
    startingPoint: str


class PlannerResult(TypedDict):
    days: list[dict[str, Any]]
    feasibility: dict[str, Any]
    recommendations: dict[str, Any]
    optimization: dict[str, Any]
    selectedCount: int
    requestedDays: int
    pace: str


PACE_STOPS = {"relaxed": 1, "balanced": 2, "active": 3}
DAY_START = {"relaxed": 600, "balanced": 540, "active": 480}
DAY_END = {"relaxed": 1080, "balanced": 1080, "active": 1140}
VISIT_BUDGET = {"relaxed": 360, "balanced": 450, "active": 540}
TRAVEL_BUDGET = {"relaxed": 180, "balanced": 300, "active": 450}
VISIT_BASE = {
    "historic-cities": 150, "archaeology": 180, "heritage": 150,
    "museums": 120, "culture": 120, "mountains-nature": 180,
    "nature": 180, "coast": 150, "mediterranean-coast": 150,
    "oases": 150, "desert": 240, "desert-expedition": 300,
}
PACE_MULTIPLIER = {"relaxed": 1.15, "balanced": 1.0, "active": 0.85}
START_COORDINATES = {
    "tripoli": (32.8872, 13.1913), "benghazi": (32.1167, 20.0667),
    "sebha": (27.0377, 14.4283),
}
ROAD_PROFILES = {
    "tripoli": ("standard", 1.0, False, False),
    "benghazi": ("standard", 1.0, False, False),
    "sabratha": ("standard", 1.0, False, False),
    "leptis-magna": ("standard", 1.0, False, False),
    "villa-sileen": ("standard", 1.05, False, False),
    "green-mountain": ("regional", 1.15, False, False),
    "bomba-bay": ("regional", 1.2, False, False),
    "nafusa": ("regional", 1.2, False, False),
    "ghadames": ("long-distance", 1.25, False, False),
    "awjila": ("remote", 1.35, False, False),
    "desert": ("desert", 1.65, True, True),
    "acacus": ("desert-expedition", 1.9, True, True),
}


def _pace(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in PACE_STOPS else "balanced"


def _js_round(value: float) -> int:
    """Match Math.round for the non-negative planner durations."""
    return int(value + 0.5)


def normalize_destination(authority: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a PlannerDestinationAuthority-shaped record for execution."""
    operational = authority.get("operational_data") or {}
    translations = authority.get("translations") or []
    english = next((item for item in translations if item.get("language_code") == "en"), {})
    opening = operational.get("opening_hours") or {}
    default_window = opening.get("default", opening) if isinstance(opening, Mapping) else {}
    result = {
        "destination_id": authority.get("destination_id"),
        "slug": authority.get("slug"),
        "category_key": authority.get("category_code"),
        "name_en": english.get("name"),
        "description_en": english.get("short_description"),
        "region_en": authority.get("region"),
        "latitude": authority.get("latitude"),
        "longitude": authority.get("longitude"),
        "recommended_visit_minutes": operational.get("recommended_visit_minutes"),
        "planner_road_access": _enum_value(operational.get("road_access")),
        "planner_road_condition": _enum_value(operational.get("road_condition")),
        "planner_priority": operational.get("planner_priority"),
        "meal_suitability": operational.get("meal_suitability"),
        "rest_suitability": operational.get("rest_suitability"),
        "planner_authority": {
            "status": "backend",
            "profileState": authority.get("profile_state", "missing"),
            "verificationStatus": _enum_value(authority.get("profile_verification_status")),
            "verifiedAt": _iso_value(authority.get("profile_verified_at")),
        },
    }
    if isinstance(default_window, Mapping):
        result["opening_time"] = default_window.get("opening_time", default_window.get("open"))
        result["closing_time"] = default_window.get("closing_time", default_window.get("close"))
    return result


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _iso_value(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def valid_coordinates(value: Mapping[str, Any] | None) -> tuple[float, float] | None:
    if not value:
        return None
    try:
        latitude, longitude = float(value.get("latitude")), float(value.get("longitude"))
    except (TypeError, ValueError):
        return None
    return (latitude, longitude) if -90 <= latitude <= 90 and -180 <= longitude <= 180 else None


def distance_km(source: Mapping[str, Any] | None, target: Mapping[str, Any] | None) -> float | None:
    start, end = valid_coordinates(source), valid_coordinates(target)
    if not start or not end:
        return None
    lat_delta, lon_delta = radians(end[0] - start[0]), radians(end[1] - start[1])
    a = sin(lat_delta / 2) ** 2 + cos(radians(start[0])) * cos(radians(end[0])) * sin(lon_delta / 2) ** 2
    return 6371 * (2 * asin(sqrt(a)))


def estimated_travel_minutes(source: Mapping[str, Any] | None, target: Mapping[str, Any] | None) -> float | None:
    distance = distance_km(source, target)
    return None if distance is None else distance / 65 * 60


def road_profile(destination: Mapping[str, Any]) -> dict[str, Any]:
    access = str(destination.get("planner_road_access") or "").lower()
    condition = str(destination.get("planner_road_condition") or "").lower()
    if access and access != "unknown":
        requires_4x4, requires_guide = access == "four_wheel_drive", access == "guided_only"
        difficult = condition in {"difficult", "very_difficult"}
        data = ("desert-expedition", 1.9) if requires_guide else (("desert", 1.65) if requires_4x4 else (("remote", 1.35) if difficult else ("standard", 1.0)))
        return {"accessClass": data[0], "roadFactor": data[1], "requires4x4": requires_4x4, "requiresGuide": requires_guide}
    profile = ROAD_PROFILES.get(str(destination.get("slug") or "").lower(), ("unknown", 1.0, False, False))
    return {"accessClass": profile[0], "roadFactor": profile[1], "requires4x4": profile[2], "requiresGuide": profile[3]}


def visit_duration_minutes(destination: Mapping[str, Any], pace: str = "balanced") -> int:
    authoritative = destination.get("recommended_visit_minutes")
    try:
        base = float(authoritative)
        if base <= 0:
            raise ValueError
    except (TypeError, ValueError):
        base = VISIT_BASE.get(str(destination.get("category_key") or "").lower(), 120)
    return _js_round(base * PACE_MULTIPLIER[_pace(pace)])


def parse_clock_minutes(value: Any) -> int | None:
    if not isinstance(value, str) or len(value.strip()) != 5 or value.strip()[2] != ":":
        return None
    try:
        hours, minutes = (int(part) for part in value.strip().split(":"))
    except ValueError:
        return None
    return hours * 60 + minutes if 0 <= hours <= 23 and 0 <= minutes <= 59 else None


def format_clock_minutes(value: Any) -> str | None:
    if not isinstance(value, (int, float)) or value < 0 or value >= 1440:
        return None
    return f"{int(value) // 60:02d}:{int(value) % 60:02d}"


def schedule_destinations(destinations: Sequence[Mapping[str, Any]], pace: str) -> list[dict[str, Any]]:
    normalized_pace, cursor, result = _pace(pace), DAY_START[_pace(pace)], []
    for destination in destinations:
        duration = visit_duration_minutes(destination, normalized_pace)
        opens, closes = parse_clock_minutes(destination.get("opening_time")), parse_clock_minutes(destination.get("closing_time"))
        known = opens is not None and closes is not None and closes > opens
        starts = max(cursor, opens) if known else cursor
        ends = starts + duration
        scheduled = ends <= DAY_END[normalized_pace] and (not known or ends <= closes)
        reason = "scheduled" if scheduled and known else "opening-hours-unknown" if scheduled else "insufficient-opening-window" if known and ends > closes else "outside-daily-window"
        result.append({"destination": destination, "scheduled": scheduled, "reason": reason, "openingStatus": "known" if known else "unknown", "startsAt": starts, "endsAt": ends, "visitMinutes": duration})
        if scheduled:
            cursor = ends
    return result


def insert_meal_rest(items: Sequence[Mapping[str, Any]], pace: str) -> list[dict[str, Any]]:
    rules = {
        "relaxed": (150, 30, 750, 870, 75), "balanced": (180, 20, 750, 840, 60),
        "active": (210, 15, 780, 840, 45),
    }[_pace(pace)]
    result, continuous, lunch_inserted = [], 0, False
    for item in items:
        if not item.get("scheduled", True):
            result.append(dict(item)); continue
        start, end = item["startsAt"], item["endsAt"]
        if not lunch_inserted and rules[2] <= start <= rules[3]:
            result.append({"type": "meal", "mealType": "lunch", "startsAt": start, "endsAt": start + rules[4], "durationMinutes": rules[4], "reason": "lunch-window"})
            lunch_inserted, continuous = True, 0
        if continuous >= rules[0]:
            result.append({"type": "rest", "startsAt": start, "endsAt": start + rules[1], "durationMinutes": rules[1], "reason": "continuous-activity-limit"})
            continuous = 0
        result.append(dict(item)); continuous += max(0, end - start)
    return result


def build_timeline(items: Sequence[Mapping[str, Any]], previous: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    prior = previous
    for item in items:
        destination = item.get("destination")
        if destination and prior:
            minutes = estimated_travel_minutes(prior, destination)
            if minutes is not None:
                factor = road_profile(destination)["roadFactor"]
                duration = _js_round(minutes * factor)
                result.append({"type": "travel", "durationMinutes": duration, "fromSlug": prior.get("slug"), "toSlug": destination.get("slug")})
        if destination:
            result.append({"type": "destination", "slug": destination.get("slug"), "scheduled": item.get("scheduled"), "startsAt": item.get("startsAt"), "endsAt": item.get("endsAt"), "durationMinutes": item.get("visitMinutes")})
            prior = destination
        else:
            result.append(dict(item))
    return result


def daily_summary(timeline: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    visit = sum(int(item.get("durationMinutes") or 0) for item in timeline if item.get("type") == "destination" and item.get("scheduled") is not False)
    travel = sum(int(item.get("durationMinutes") or 0) for item in timeline if item.get("type") == "travel")
    recovery = sum(int(item.get("durationMinutes") or 0) for item in timeline if item.get("type") in {"meal", "rest"})
    stop_count = sum(1 for item in timeline if item.get("type") == "destination" and item.get("scheduled") is not False)
    total = visit + travel + recovery
    intensity = "high" if total > 540 or stop_count >= 3 else "moderate" if total > 300 or stop_count == 2 else "low"
    return {"stopCount": stop_count, "visitMinutes": visit, "travelMinutes": travel, "recoveryMinutes": recovery, "totalPlannedMinutes": total, "intensity": intensity}


def trip_feasibility(days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unscheduled = sum(1 for day in days for destination in day.get("destinations", []) if destination.get("planner_score", {}).get("scheduled") is False)
    overloaded = sum(1 for day in days if day.get("summary", {}).get("intensity") == "high")
    score = max(0, 100 - unscheduled * 20 - overloaded * 15)
    rating = "excellent" if score >= 85 else "good" if score >= 70 else "challenging" if score >= 50 else "not-feasible"
    return {"score": score, "rating": rating, "evidence": {"unscheduledStopCount": unscheduled, "overloadedDayCount": overloaded}}


def recommendations(days: Sequence[Mapping[str, Any]], feasibility: Mapping[str, Any]) -> dict[str, Any]:
    items = []
    if feasibility["evidence"]["unscheduledStopCount"]:
        items.append({"type": "schedule", "priority": "high", "message": "Remove or reschedule stops outside operating windows."})
    if feasibility["evidence"]["overloadedDayCount"]:
        items.append({"type": "pace", "priority": "high", "message": "Reduce high-intensity days."})
    return {"recommendations": items, "count": len(items)}


def optimize(days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    optimized = deepcopy(list(days)); actions: list[str] = []
    for day in optimized:
        scheduled_slugs = {
            item.get("slug") or (item.get("destination") or {}).get("slug")
            for item in day.get("timeline", [])
            if item.get("type") == "destination" and item.get("scheduled") is not False
        }
        filtered = [item for item in day.get("destinations", []) if item.get("slug") in scheduled_slugs]
        if len(filtered) != len(day.get("destinations", [])):
            day["destinations"] = filtered
            if "remove-unscheduled-stops" not in actions: actions.append("remove-unscheduled-stops")
        if day.get("summary", {}).get("intensity") == "high" and len(day.get("destinations", [])) > 1:
            day["destinations"].sort(key=lambda item: (-float(item.get("planner_score", {}).get("total", 0)), str(item.get("slug", ""))))
            day["destinations"] = day["destinations"][:-1]
            if "reduce-high-intensity-days" not in actions: actions.append("reduce-high-intensity-days")
    before = sum(len(day.get("destinations", [])) for day in days)
    after = sum(len(day.get("destinations", [])) for day in optimized)
    return {"actions": actions, "optimizedDays": optimized, "summary": {"changed": before != after, "originalDestinationCount": before, "optimizedDestinationCount": after, "removedDestinationCount": before - after, "actionCount": len(actions)}, "recommended": bool(actions)}


def execute_planner(destinations: Iterable[Mapping[str, Any]], preferences: PlannerPreferences | None = None) -> PlannerResult:
    """Execute the minimum deterministic backend planner pipeline."""
    prefs = preferences or {}
    pace = _pace(prefs.get("pace")); raw_days = prefs.get("days", 3)
    days_count = max(1, min(14, raw_days if isinstance(raw_days, int) else 3))
    normalized = [normalize_destination(item) if "operational_data" in item else dict(item) for item in destinations]
    normalized = [item for item in normalized if item.get("slug") and item.get("category_key")]
    normalized.sort(key=lambda item: (-float(item.get("planner_priority") or 0), str(item["slug"])))
    selected = normalized[:days_count * PACE_STOPS[pace]]
    days: list[dict[str, Any]] = []
    for index in range(days_count):
        batch = selected[index * PACE_STOPS[pace]:(index + 1) * PACE_STOPS[pace]]
        scheduled = schedule_destinations(batch, pace)
        enriched = []
        for item in scheduled:
            destination = deepcopy(dict(item["destination"]))
            destination["planner_score"] = {"estimatedVisitMinutes": item["visitMinutes"], "scheduled": item["scheduled"], "scheduledStartMinutes": item["startsAt"], "scheduledEndMinutes": item["endsAt"], "scheduledStart": format_clock_minutes(item["startsAt"]), "scheduledEnd": format_clock_minutes(item["endsAt"]), "openingHoursStatus": item["openingStatus"], "scheduleReason": item["reason"], "total": float(destination.get("planner_priority") or 0)}
            enriched.append(destination)
        timeline = build_timeline(insert_meal_rest(scheduled, pace))
        summary = daily_summary(timeline)
        used = sum(visit_duration_minutes(item, pace) for item in batch)
        days.append({"dayNumber": index + 1, "type": "visit", "destinations": enriched, "visitBudget": {"usedMinutes": used, "budgetMinutes": VISIT_BUDGET[pace], "remainingMinutes": max(0, VISIT_BUDGET[pace] - used), "exceedsBudget": used > VISIT_BUDGET[pace]}, "timeline": timeline, "summary": summary})
    feasibility = trip_feasibility(days)
    recommendation_result = recommendations(days, feasibility)
    optimization = optimize(days)
    return {"days": days, "feasibility": feasibility, "recommendations": recommendation_result, "optimization": optimization, "selectedCount": len(selected), "requestedDays": days_count, "pace": pace}
