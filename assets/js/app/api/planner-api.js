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
