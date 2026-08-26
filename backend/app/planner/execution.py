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
REGION_DESTINATIONS = {
    "northwest": {"tripoli", "sabratha", "leptis-magna", "villa-sileen", "nafusa"},
    "east": {"benghazi", "green-mountain", "bomba-bay"},
    "easternOases": {"awjila"}, "westernDesert": {"ghadames"},
    "southwest": {"acacus", "desert"},
}
START_REGIONS = {"tripoli": "northwest", "benghazi": "east", "sebha": "southwest"}
REGION_NEIGHBORS = {
    "northwest": {"westernDesert"}, "east": {"easternOases"},
    "easternOases": {"east", "southwest"},
    "westernDesert": {"northwest", "southwest"},
    "southwest": {"westernDesert", "easternOases"},
}
ROUTE_ORDER = {
    "northwest": ["tripoli", "leptis-magna", "villa-sileen", "sabratha", "nafusa"],
    "east": ["benghazi", "green-mountain", "bomba-bay"],
    "easternOases": ["awjila"], "westernDesert": ["ghadames"],
    "southwest": ["desert", "acacus"],
}
INTEREST_CATEGORIES = {
    "history": {"historic-cities", "archaeological-sites", "oases-heritage", "mountains-heritage"},
    "heritage": {"historic-cities", "archaeological-sites", "oases-heritage", "mountains-heritage", "sahara-rock-art"},
    "archaeology": {"archaeological-sites", "sahara-rock-art"},
    "desert": {"sahara-desert", "sahara-rock-art", "oases-heritage", "oases-nature"},
    "nature": {"mountains-nature", "mediterranean-coast", "oases-nature", "sahara-desert"},
    "coast": {"mediterranean-coast"},
    "culture": {"historic-cities", "oases-heritage", "mountains-heritage"},
}
START_KEYWORDS = {
    "tripoli": ["tripoli", "northwest", "western", "طرابلس", "شمال غرب", "الغربية"],
    "benghazi": ["benghazi", "eastern", "northeast", "cyrenaica", "بنغازي", "شرق", "برقة"],
    "sebha": ["fezzan", "southern", "southwest", "sahara", "فزان", "جنوب", "الصحراء"],
}
TRAVELER_CATEGORIES = {
    "family": {"historic-cities", "archaeological-sites", "mountains-nature", "mediterranean-coast", "oases-nature"},
    "couple": {"historic-cities", "mountains-nature", "mediterranean-coast", "oases-heritage"},
    "solo": {"historic-cities", "archaeological-sites", "mountains-heritage", "sahara-rock-art", "sahara-desert"},
    "group": {"archaeological-sites", "sahara-rock-art", "sahara-desert", "mountains-nature"},
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


def destination_region(destination: Mapping[str, Any]) -> str:
    slug = str(destination.get("slug") or "").strip().lower()
    return next((region for region, slugs in REGION_DESTINATIONS.items() if slug in slugs), "unknown")


def region_relationship(source: str, target: str) -> str:
    if not source or not target or "unknown" in {source, target}:
        return "unknown"
    if source == target:
        return "same"
    return "adjacent" if target in REGION_NEIGHBORS.get(source, set()) else "distant"


def max_major_regions(days: Any) -> int:
    try:
        value = float(days)
    except (TypeError, ValueError):
        return 1
    return 1 if value <= 3 else 2 if value <= 6 else 3


def geographic_penalty(destination: Mapping[str, Any], starting_point: Any, days: Any) -> int:
    relationship = region_relationship(
        START_REGIONS.get(str(starting_point or "").strip().lower(), "unknown"),
        destination_region(destination),
    )
    if relationship == "same": return 0
    if relationship == "adjacent": return 30 if max_major_regions(days) == 1 else 8
    if relationship == "distant": return 70 if float(days or 0) <= 3 else 40 if float(days or 0) <= 6 else 15
    return 10


def travel_time_penalty(source: Mapping[str, Any] | None, target: Mapping[str, Any], days: Any, pace: str) -> dict[str, Any]:
    minutes = estimated_travel_minutes(source, target)
    if minutes is None:
        return {"minutes": None, "band": "unknown", "penalty": 0, "exceedsDailyBudget": False}
    band = "short" if minutes <= 90 else "moderate" if minutes <= 180 else "long" if minutes <= 360 else "very-long"
    exceeds = minutes > TRAVEL_BUDGET[_pace(pace)]
    penalty = 5 if band == "moderate" else (35 if float(days or 1) <= 3 else 15) if band == "long" else (90 if float(days or 1) <= 3 else 55 if float(days or 1) <= 6 else 25) if band == "very-long" else 0
    return {"minutes": minutes, "band": band, "penalty": penalty + (15 if exceeds else 0), "exceedsDailyBudget": exceeds}


def score_destination(destination: Mapping[str, Any], preferences: Mapping[str, Any]) -> dict[str, Any]:
    interests = [str(value).strip().lower() for value in preferences.get("interests", []) if str(value).strip()]
    category = str(destination.get("category_key") or "").strip().lower()
    matches = sum(category in INTEREST_CATEGORIES.get(interest, set()) for interest in interests)
    interest_score = min(40, _js_round(matches / len(interests) * 40)) if matches and interests else 0
    searchable = " ".join(str(destination.get(key) or "") for key in ("slug", "name_en", "name_ar", "description_en", "description_ar", "region_en", "region_ar", "category_en", "category_ar", "category_key")).lower()
    start = str(preferences.get("startingPoint") or "").strip().lower()
    starting_score = 25 if any(keyword.lower() in searchable for keyword in START_KEYWORDS.get(start, [])) else 0
    traveler = str(preferences.get("travelerType") or "").strip().lower()
    traveler_score = 10 if category in TRAVELER_CATEGORIES.get(traveler, set()) else 0
    content_score = 5 if destination.get("description_en") or destination.get("description_ar") else 0
    regional = geographic_penalty(destination, start, preferences.get("days", 1))
    origin_coordinates = START_COORDINATES.get(start)
    origin = {"latitude": origin_coordinates[0], "longitude": origin_coordinates[1]} if origin_coordinates else None
    travel = travel_time_penalty(origin, destination, preferences.get("days", 1), str(preferences.get("pace") or "balanced"))
    road = road_profile(destination)
    road_penalties = {"standard": 0, "regional": 3, "long-distance": 5, "remote": 10, "desert": 18, "desert-expedition": 25}
    road_penalty = road_penalties.get(road["accessClass"], 0)
    distance = distance_km(origin, destination)
    travel_penalty = travel["penalty"] + road_penalty if travel["minutes"] is not None else regional + road_penalty
    tourism = interest_score + starting_score + traveler_score + content_score
    return {
        "total": tourism - travel_penalty, "tourismScore": tourism,
        "interestScore": interest_score, "startingRegionScore": starting_score,
        "travelerScore": traveler_score, "contentScore": content_score,
        "geographicPenalty": regional, "coordinatePenalty": None if distance is None else 0,
        "distanceKm": distance, "travelTimeMinutes": travel["minutes"],
        "adjustedRoadTravelMinutes": None if travel["minutes"] is None else travel["minutes"] * road["roadFactor"],
        "travelTimeBand": travel["band"], "travelTimePenalty": None if travel["minutes"] is None else travel["penalty"],
        "roadFeasibilityPenalty": road_penalty, "roadAccessClass": road["accessClass"],
        "roadFactor": road["roadFactor"], "requires4x4": road["requires4x4"],
        "requiresGuide": road["requiresGuide"], "exceedsDailyTravelBudget": None if travel["minutes"] is None else travel["exceedsDailyBudget"],
        "routingMode": "travel-time" if travel["minutes"] is not None else "region",
        "geographicRegion": destination_region(destination),
    }


def rank_destinations(destinations: Iterable[Mapping[str, Any]], preferences: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries = [{"destination": dict(item), "score": score_destination(item, preferences)} for item in destinations if item.get("slug") and item.get("category_key")]
    return sorted(entries, key=lambda item: (-item["score"]["total"], str(item["destination"]["slug"])))


def order_nearest(destinations: Sequence[Mapping[str, Any]], start: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    remaining, ordered, current = list(destinations), [], start
    if valid_coordinates(current) is None: return remaining
    while remaining:
        candidates = [(distance_km(current, item), index) for index, item in enumerate(remaining) if valid_coordinates(item)]
        candidates = [(distance, index) for distance, index in candidates if distance is not None]
        if not candidates: ordered.extend(remaining); break
        _, index = min(candidates, key=lambda value: value[0])
        item = remaining.pop(index); ordered.append(item); current = item
    return ordered


def route_order(entries: Sequence[Mapping[str, Any]], preferences: Mapping[str, Any]) -> list[dict[str, Any]]:
    origin_region = START_REGIONS.get(str(preferences.get("startingPoint") or "").lower(), "unknown")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for entry in entries: grouped.setdefault(destination_region(entry["destination"]), []).append(entry)
    regions = [origin_region] + [region for region in grouped if region != origin_region]
    coordinates = START_COORDINATES.get(str(preferences.get("startingPoint") or "").lower())
    current = {"latitude": coordinates[0], "longitude": coordinates[1]} if coordinates else None
    result = []
    for region in regions:
        group = grouped.get(region, [])
        if not group: continue
        destinations = [entry["destination"] for entry in group]
        if current and any(valid_coordinates(item) for item in destinations):
            destinations = order_nearest(destinations, current)
        else:
            route = ROUTE_ORDER.get(region, [])
            destinations = sorted(destinations, key=lambda item: (route.index(item["slug"]) if item["slug"] in route else float("inf"), str(item["slug"])))
        lookup = {str(entry["destination"]["slug"]).lower(): entry for entry in group}
        for destination in destinations:
            result.append(dict(lookup[str(destination["slug"]).lower()]))
            if valid_coordinates(destination): current = destination
    return result


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


def timeline_duration(item: Mapping[str, Any]) -> float | None:
    explicit = item.get("durationMinutes")
    if isinstance(explicit, (int, float)) and explicit >= 0: return explicit
    start, end = item.get("startsAt"), item.get("endsAt")
    return end - start if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end >= start else None


def resolve_timeline_conflicts(timeline: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result, cursor = [], None
    for raw in timeline:
        if not raw: continue
        item = deepcopy(dict(raw)); start, end = item.get("startsAt"), item.get("endsAt")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            result.append(item); continue
        if cursor is not None and start < cursor:
            duration = timeline_duration(item)
            if duration is not None:
                start, end = cursor, cursor + duration
                item.update({"startsAt": start, "endsAt": end, "conflictAdjusted": True})
        else: item["conflictAdjusted"] = False
        item["startsAtLabel"], item["endsAtLabel"] = format_clock_minutes(start), format_clock_minutes(end)
        result.append(item); cursor = end
    return result


def build_timeline(items: Sequence[Mapping[str, Any]], previous: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    normalized = [deepcopy(dict(item)) for item in items if item]
    result, prior = [], previous
    for item in normalized:
        destination = item.get("destination")
        if destination and prior:
            minutes = estimated_travel_minutes(prior, destination)
            if minutes is not None and isinstance(item.get("startsAt"), (int, float)):
                duration = max(0, _js_round(minutes * road_profile(destination)["roadFactor"]))
                start = result[-1].get("endsAt") if result else item["startsAt"]
                if not isinstance(start, (int, float)): start = item["startsAt"]
                result.append({"type": "travel", "fromDestination": prior, "toDestination": destination, "startsAt": start, "endsAt": start + duration, "durationMinutes": duration, "startsAtLabel": format_clock_minutes(start), "endsAtLabel": format_clock_minutes(start + duration)})
        if destination:
            item.setdefault("type", "destination"); prior = destination
        result.append(item)
    priority = {"travel": 1, "meal": 2, "rest": 3, "destination": 4}
    result.sort(key=lambda item: (item.get("startsAt") if isinstance(item.get("startsAt"), (int, float)) else float("inf"), priority.get(item.get("type"), 99)))
    return resolve_timeline_conflicts(result)


def daily_summary(timeline: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = lambda kind: sum(timeline_duration(item) or 0 for item in timeline if item.get("type") == kind)
    timed_start = [item.get("startsAt") for item in timeline if isinstance(item.get("startsAt"), (int, float))]
    timed_end = [item.get("endsAt") for item in timeline if isinstance(item.get("endsAt"), (int, float))]
    visit, travel, meal, rest = values("destination"), values("travel"), values("meal"), values("rest")
    starts, ends = (timed_start[0] if timed_start else None), (timed_end[-1] if timed_end else None)
    total = ends - starts if starts is not None and ends is not None and ends >= starts else 0
    activity, recovery = visit + travel, meal + rest
    intensity = "unknown" if total <= 0 else "high" if activity >= 480 and recovery < 60 else "moderate" if activity >= 330 else "light"
    return {"stopCount": sum(item.get("type") == "destination" for item in timeline), "visitMinutes": visit, "travelMinutes": travel, "mealMinutes": meal, "restMinutes": rest, "startsAt": starts, "endsAt": ends, "totalDayMinutes": total, "activityMinutes": activity, "recoveryMinutes": recovery, "intensity": intensity}


def trip_feasibility(days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    destinations = [item for day in days for item in day.get("destinations", [])]
    evidence = {
        "dayCount": len(days), "destinationCount": len(destinations),
        "unscheduledStops": sum(item.get("type") == "destination" and item.get("scheduled") is False for day in days for item in day.get("timeline", [])),
        "highIntensityDays": sum(day.get("summary", {}).get("intensity") == "high" for day in days),
        "moderateIntensityDays": sum(day.get("summary", {}).get("intensity") == "moderate" for day in days),
        "longTravelDays": sum(float(day.get("summary", {}).get("travelMinutes") or 0) >= 360 for day in days),
        "specialAccessStops": sum(bool(item.get("planner_score", {}).get("requires4x4") or item.get("planner_score", {}).get("requiresGuide")) for item in destinations),
        "conflictAdjustedItems": sum(bool(item.get("conflictAdjusted")) for day in days for item in day.get("timeline", [])),
        "totalTravelMinutes": sum(float(day.get("summary", {}).get("travelMinutes") or 0) for day in days),
        "totalVisitMinutes": sum(float(day.get("summary", {}).get("visitMinutes") or 0) for day in days),
        "totalRecoveryMinutes": sum(float(day.get("summary", {}).get("recoveryMinutes") or 0) for day in days),
    }
    penalty = evidence["unscheduledStops"] * 18 + evidence["highIntensityDays"] * 8 + evidence["longTravelDays"] * 7 + evidence["specialAccessStops"] * 3 + min(evidence["conflictAdjustedItems"] * 2, 8)
    if evidence["totalTravelMinutes"] > 0 and evidence["totalVisitMinutes"] > 0 and evidence["totalTravelMinutes"] > evidence["totalVisitMinutes"] * .9: penalty += 8
    if evidence["totalRecoveryMinutes"] / max(1, evidence["dayCount"]) < 30: penalty += 5
    penalty, score = min(100, _js_round(penalty)), max(0, 100 - min(100, _js_round(penalty)))
    rating = "excellent" if score >= 90 else "good" if score >= 75 else "fair" if score >= 60 else "needs-review"
    warnings, strengths = [], []
    (warnings if evidence["unscheduledStops"] else strengths).append("unscheduled-stops" if evidence["unscheduledStops"] else "all-stops-scheduled")
    (warnings if evidence["highIntensityDays"] else strengths).append("high-intensity-days" if evidence["highIntensityDays"] else "balanced-daily-intensity")
    if evidence["longTravelDays"]: warnings.append("long-travel-days")
    if evidence["specialAccessStops"]: warnings.append("special-access-required")
    if not evidence["conflictAdjustedItems"]: strengths.append("no-timeline-conflicts")
    if evidence["totalRecoveryMinutes"] > 0: strengths.append("recovery-time-included")
    return {"score": score, "rating": rating, "penalty": penalty, "warnings": warnings, "strengths": strengths, "evidence": evidence}


def recommendations(days: Sequence[Mapping[str, Any]], feasibility: Mapping[str, Any]) -> dict[str, Any]:
    high = [{"dayNumber": day.get("dayNumber"), "activityMinutes": float(day.get("summary", {}).get("activityMinutes") or 0), "recoveryMinutes": float(day.get("summary", {}).get("recoveryMinutes") or 0)} for day in days if day.get("summary", {}).get("intensity") == "high"]
    long = [{"dayNumber": day.get("dayNumber"), "travelMinutes": float(day.get("summary", {}).get("travelMinutes") or 0)} for day in days if float(day.get("summary", {}).get("travelMinutes") or 0) >= 360]
    unscheduled = [{"dayNumber": day.get("dayNumber"), "slug": (item.get("destination") or {}).get("slug"), "reason": item.get("reason")} for day in days for item in day.get("timeline", []) if item.get("type") == "destination" and item.get("scheduled") is False]
    special = [{"dayNumber": day.get("dayNumber"), "slug": item.get("slug"), "requires4x4": bool(item.get("planner_score", {}).get("requires4x4")), "requiresGuide": bool(item.get("planner_score", {}).get("requiresGuide"))} for day in days for item in day.get("destinations", []) if item.get("planner_score", {}).get("requires4x4") or item.get("planner_score", {}).get("requiresGuide")]
    average = sum(float(day.get("summary", {}).get("recoveryMinutes") or 0) for day in days) / len(days) if days else 0
    evidence = {"feasibilityScore": float(feasibility.get("score") or 0), "feasibilityRating": feasibility.get("rating", "unknown"), "highIntensityDays": high, "longTravelDays": long, "unscheduledStops": unscheduled, "specialAccessStops": special, "averageRecoveryMinutes": average}
    items = []
    if unscheduled: items.append({"code": "review-unscheduled-stops", "priority": "high", "evidence": {"stops": unscheduled}})
    if long: items.append({"code": "separate-long-travel", "priority": "high", "evidence": {"days": long}})
    if high: items.append({"code": "reduce-day-intensity", "priority": "medium", "evidence": {"days": high}})
    if average < 30: items.append({"code": "increase-recovery-time", "priority": "medium", "evidence": {"averageRecoveryMinutes": _js_round(average)}})
    if special: items.append({"code": "prepare-special-access", "priority": "medium", "evidence": {"stops": special}})
    if evidence["feasibilityScore"] >= 90 and not any(item["priority"] == "high" for item in items): items.append({"code": "itinerary-well-balanced", "priority": "info", "evidence": {"score": evidence["feasibilityScore"]}})
    return {"evidence": evidence, "recommendations": items}


def optimize(days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    original, optimized = deepcopy(list(days)), deepcopy(list(days)); actions: list[str] = []
    overloaded = [day.get("dayNumber") for day in original if day.get("summary", {}).get("intensity") == "high"]
    unscheduled_evidence = [{"dayNumber": day.get("dayNumber"), "slug": (item.get("destination") or {}).get("slug")} for day in original for item in day.get("timeline", []) if item.get("type") == "destination" and item.get("scheduled") is False]
    long_travel = [{"dayNumber": day.get("dayNumber"), "travelMinutes": float(day.get("summary", {}).get("travelMinutes") or 0)} for day in original if float(day.get("summary", {}).get("travelMinutes") or 0) >= 360]
    for day in optimized:
        unscheduled_slugs = {(item.get("destination") or {}).get("slug") for item in day.get("timeline", []) if item.get("type") == "destination" and item.get("scheduled") is False}
        filtered = [item for item in day.get("destinations", []) if item.get("slug") not in unscheduled_slugs]
        if len(filtered) != len(day.get("destinations", [])):
            day["destinations"] = filtered
            if "remove-unscheduled-stops" not in actions: actions.append("remove-unscheduled-stops")
        if day.get("summary", {}).get("intensity") == "high" and len(day.get("destinations", [])) > 1:
            lowest = min(day["destinations"], key=lambda item: float(item.get("planner_score", {}).get("total", 0)))
            day["destinations"] = [item for item in day["destinations"] if str(item.get("slug", "")).lower() != str(lowest.get("slug", "")).lower()]
            if "reduce-high-intensity-days" not in actions: actions.append("reduce-high-intensity-days")
    if long_travel: actions.append("review-long-travel-days")
    before = sum(len(day.get("destinations", [])) for day in days)
    after = sum(len(day.get("destinations", [])) for day in optimized)
    return {"originalDays": original, "actions": actions, "evidence": {"overloadedDays": overloaded, "unscheduledStops": unscheduled_evidence, "longTravelDays": long_travel}, "optimizedDays": optimized, "summary": {"changed": original != optimized, "originalDestinationCount": before, "optimizedDestinationCount": after, "removedDestinationCount": max(0, before - after), "actionCount": len(actions)}}


def rebuild_visit_day(day: Mapping[str, Any], pace: str) -> dict[str, Any]:
    copy = deepcopy(dict(day)); destinations = list(copy.get("destinations", []))
    scheduled = schedule_destinations(destinations, pace); enriched = []
    for item in scheduled:
        destination = deepcopy(dict(item["destination"])); score = dict(destination.get("planner_score", {}))
        score.update({"estimatedVisitMinutes": item["visitMinutes"], "scheduled": item["scheduled"], "scheduledStartMinutes": item["startsAt"], "scheduledEndMinutes": item["endsAt"], "scheduledStart": format_clock_minutes(item["startsAt"]), "scheduledEnd": format_clock_minutes(item["endsAt"]), "openingHoursStatus": item["openingStatus"], "scheduleReason": item["reason"]})
        destination["planner_score"] = score; enriched.append(destination)
    copy["destinations"] = enriched
    used, budget = sum(visit_duration_minutes(item, pace) for item in destinations), VISIT_BUDGET[_pace(pace)]
    copy["visitBudget"] = {"usedMinutes": used, "budgetMinutes": budget, "remainingMinutes": max(0, budget - used), "exceedsBudget": used > budget}
    timeline_items = []
    for item in insert_meal_rest(scheduled, pace):
        if item.get("type") in {"meal", "rest"}: timeline_items.append(item)
        else: timeline_items.append({"type": "destination", "destination": item["destination"], "scheduled": item["scheduled"], "reason": item["reason"], "openingStatus": item["openingStatus"], "startsAt": item["startsAt"], "endsAt": item["endsAt"]})
    copy["timeline"] = build_timeline(timeline_items); copy["summary"] = daily_summary(copy["timeline"])
    return copy


def rebuild_days(days: Sequence[Mapping[str, Any]], pace: str) -> list[dict[str, Any]]:
    result = []
    for raw in days:
        if raw.get("type") != "travel": result.append(rebuild_visit_day(raw, pace)); continue
        day = deepcopy(dict(raw)); budget = VISIT_BUDGET[_pace(pace)]
        day["visitBudget"] = {"usedMinutes": 0, "budgetMinutes": budget, "remainingMinutes": budget, "exceedsBudget": False}
        day.setdefault("timeline", []); day.setdefault("summary", {"stopCount": 0, "visitMinutes": 0, "travelMinutes": 0, "mealMinutes": 0, "restMinutes": 0, "startsAt": None, "endsAt": None, "totalDayMinutes": 0, "activityMinutes": 0, "recoveryMinutes": 0, "intensity": "unknown"})
        result.append(day)
    return result


def evaluate_optimization(original: Sequence[Mapping[str, Any]], optimized: Sequence[Mapping[str, Any]], pace: str) -> dict[str, Any]:
    after_days = rebuild_days(optimized, pace); before_feasibility, after_feasibility = trip_feasibility(original), trip_feasibility(after_days)
    delta = after_feasibility["score"] - before_feasibility["score"]
    count = lambda days: sum(len(day.get("destinations", [])) for day in days)
    return {"before": {"days": deepcopy(list(original)), "feasibility": before_feasibility, "destinationCount": count(original)}, "after": {"days": after_days, "feasibility": after_feasibility, "destinationCount": count(after_days)}, "improvement": {"scoreDelta": delta, "improved": delta > 0, "unchanged": delta == 0, "worsened": delta < 0}}


def execute_planner(destinations: Iterable[Mapping[str, Any]], preferences: PlannerPreferences | None = None) -> PlannerResult:
    """Execute the deterministic backend equivalent of buildSuggestedItinerary."""
    prefs = preferences or {}
    pace = _pace(prefs.get("pace")); raw_days = prefs.get("days", 3)
    days_count = max(1, min(14, raw_days if isinstance(raw_days, int) else 3))
    normalized = [normalize_destination(item) if "operational_data" in item else dict(item) for item in destinations]
    execution_prefs = {**prefs, "days": days_count, "pace": pace}
    ranked = rank_destinations(normalized, execution_prefs)
    maximum, origin_region, selected_regions, selected = days_count * PACE_STOPS[pace], START_REGIONS.get(str(prefs.get("startingPoint") or "").lower(), "unknown"), set(), []
    if origin_region != "unknown": selected_regions.add(origin_region)
    for entry in ranked:
        if len(selected) >= maximum: break
        if entry["score"]["total"] <= 0: continue
        region = destination_region(entry["destination"])
        if region != "unknown" and region not in selected_regions and len(selected_regions) >= max_major_regions(days_count): continue
        selected.append(entry)
        if region != "unknown": selected_regions.add(region)
    ordered = route_order(selected, execution_prefs)
    days = [{"dayNumber": index + 1, "type": "visit", "destinations": []} for index in range(days_count)]
    index = stops = 0; previous = None
    for entry in ordered:
        destination = entry["destination"]
        if previous:
            minutes = estimated_travel_minutes(previous, destination)
            reserve = minutes > TRAVEL_BUDGET[pace] if minutes is not None else region_relationship(destination_region(previous), destination_region(destination)) == "distant"
            if reserve:
                if stops > 0: index += 1; stops = 0
                if index >= days_count: break
                days[index] = {"dayNumber": index + 1, "type": "travel", "fromRegion": destination_region(previous), "toRegion": destination_region(destination), "destinations": []}
                index += 1; stops = 0
                if index >= days_count: break
        if stops >= PACE_STOPS[pace]: index += 1; stops = 0
        if index >= days_count: break
        enriched = deepcopy(destination); enriched["planner_score"] = deepcopy(entry["score"])
        days[index]["destinations"].append(enriched); previous = destination; stops += 1
    days = rebuild_days(days, pace)
    feasibility = trip_feasibility(days)
    recommendation_result = recommendations(days, feasibility)
    structure = optimize(days); evaluation = evaluate_optimization(structure["originalDays"], structure["optimizedDays"], pace)
    optimization = {"actions": structure["actions"], "evidence": structure["evidence"], "summary": structure["summary"], "before": evaluation["before"], "after": evaluation["after"], "improvement": evaluation["improvement"], "safeToApply": not evaluation["improvement"]["worsened"], "recommended": evaluation["improvement"]["improved"]}
    return {"days": days, "feasibility": feasibility, "recommendations": recommendation_result, "optimization": optimization, "selectedCount": sum(len(day["destinations"]) for day in days), "requestedDays": days_count, "pace": pace}
