import assert from "node:assert/strict";
import test from "node:test";

import {
  applyPlannerProfile,
  enrichPlannerDestinationsWithAuthority,
  plannerRunPayload,
} from "../assets/js/app/ai/planner-authority-adapter.js";


test("backend planner profile maps operational fields without replacing identity", () => {
  const result = applyPlannerProfile(
    { destination_id: 7, slug: "leptis-magna", name_en: "Leptis Magna" },
    {
      destination_id: 7,
      recommended_visit_minutes: 180,
      opening_hours: { default: { open: "09:00", close: "17:00" } },
      planner_priority: 80,
      access_status: "open",
      road_access: "standard",
      road_surface: "paved",
      road_condition: "good",
      meal_suitability: 20,
      rest_suitability: 30,
      verification_status: "unverified",
      verified_at: null,
    },
  );
  assert.equal(result.slug, "leptis-magna");
  assert.equal(result.recommended_visit_minutes, 180);
  assert.equal(result.opening_time, "09:00");
  assert.equal(result.planner_authority.verificationStatus, "unverified");
});


test("unavailable backend profile preserves deterministic fallback", async () => {
  const result = await enrichPlannerDestinationsWithAuthority(
    [{ slug: "tripoli", category_key: "historic-cities" }],
    {
      listDestinationCatalogue: async () => ({
        items: [{ id: 3, slug: "tripoli", latitude: 32.8, longitude: 13.1 }],
        pages: 1,
      }),
      getDestinationPlannerProfile: async () => { throw new Error("offline"); },
    },
  );
  assert.equal(result[0].destination_id, 3);
  assert.equal(result[0].latitude, 32.8);
  assert.equal(result[0].planner_authority.status, "fallback");
});


test("planner run payload contains snapshots but never a user id", () => {
  const payload = plannerRunPayload({
    requestedDays: 2,
    selectedCount: 1,
    preferences: { pace: "balanced" },
    days: [{ dayNumber: 1 }],
    feasibility: { score: 88 },
    recommendations: { recommendations: [] },
    optimization: { safeToApply: true },
  });
  assert.equal(payload.feasibility_score, 88);
  assert.equal(payload.trip_id, null);
  assert.equal(Object.hasOwn(payload, "user_id"), false);
});
