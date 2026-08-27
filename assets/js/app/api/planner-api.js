import { apiClient } from "./client.js";

export function getDestinationPlannerProfile(destinationId, options = {}) {
  return apiClient.get(
    `/destinations/${encodeURIComponent(destinationId)}/planner-profile`,
    options,
  );
}

export function createPlannerRun(payload, options = {}) {
  return apiClient.post("/planner-runs", payload, options);
}
export function executeTripPlanner(tripId, payload, options = {}) {
  const normalizedTripId = Number(tripId);

  if (
    !Number.isSafeInteger(normalizedTripId) ||
    normalizedTripId < 1
  ) {
    throw new TypeError("A valid trip ID is required");
  }

  return apiClient.post(
    `/trips/${encodeURIComponent(normalizedTripId)}/planner-runs/execute`,
    payload,
    options,
  );
}
