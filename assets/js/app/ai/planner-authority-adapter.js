import { enrichPlannerDestinationsWithCoordinates } from "./coordinate-enrichment.js";

function defaultOpeningWindow(openingHours) {
  if (!openingHours || typeof openingHours !== "object") return {};
  const candidate = openingHours.default ?? openingHours;
  const opening = candidate.opening_time ?? candidate.openingTime ?? candidate.open ?? null;
  const closing = candidate.closing_time ?? candidate.closingTime ?? candidate.close ?? null;
  return typeof opening === "string" && typeof closing === "string"
    ? { opening_time: opening, closing_time: closing }
    : {};
}

export function applyPlannerProfile(destination, profile) {
  if (!profile || profile.destination_id !== destination.destination_id) {
    return { ...destination, planner_authority: { status: "fallback", reason: "missing" } };
  }
  return {
    ...destination,
    ...defaultOpeningWindow(profile.opening_hours),
    recommended_visit_minutes: profile.recommended_visit_minutes ?? null,
    planner_priority: profile.planner_priority,
    planner_access_status: profile.access_status,
    planner_road_access: profile.road_access,
    planner_road_surface: profile.road_surface,
    planner_road_condition: profile.road_condition,
    meal_suitability: profile.meal_suitability,
    rest_suitability: profile.rest_suitability,
    planner_authority: {
      status: "backend",
      verificationStatus: profile.verification_status,
      verifiedAt: profile.verified_at ?? null,
    },
  };
}

export async function enrichPlannerDestinationsWithAuthority(
  destinations,
  { listDestinationCatalogue, getDestinationPlannerProfile },
) {
  const coordinated = await enrichPlannerDestinationsWithCoordinates(destinations, {
    listDestinationCatalogue,
  });
  if (typeof getDestinationPlannerProfile !== "function") return coordinated;

  return Promise.all(coordinated.map(async (destination) => {
    if (!destination.destination_id) return { ...destination };
    try {
      const profile = await getDestinationPlannerProfile(destination.destination_id);
      return applyPlannerProfile(destination, profile);
    } catch {
      return {
        ...destination,
        planner_authority: { status: "fallback", reason: "unavailable" },
      };
    }
  }));
}

export function plannerRunPayload(itinerary) {
  return {
    trip_id: null,
    input_snapshot: { preferences: itinerary.preferences, requested_days: itinerary.requestedDays },
    itinerary_snapshot: { days: itinerary.days, selected_count: itinerary.selectedCount },
    feasibility_snapshot: itinerary.feasibility ?? {},
    recommendations_snapshot: itinerary.recommendations ?? {},
    optimization_snapshot: itinerary.optimization ?? {},
    feasibility_score: Number.isFinite(Number(itinerary.feasibility?.score))
      ? Number(itinerary.feasibility.score)
      : null,
  };
}
