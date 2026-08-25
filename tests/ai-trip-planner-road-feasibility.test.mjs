import assert from "node:assert/strict";
import test from "node:test";

import {
  adjustedRoadTravelMinutes,
  destinationAccessProfile,
  requiresSpecialAccess,
  roadFeasibilityEvidence,
  roadFeasibilityPenalty,
} from "../assets/js/app/ai/road-feasibility.js";


test("Tripoli uses standard access profile", () => {
  const profile =
    destinationAccessProfile({
      slug: "tripoli",
    });

  assert.equal(
    profile.accessClass,
    "standard",
  );

  assert.equal(
    profile.requires4x4,
    false,
  );
});


test("Acacus is classified as desert expedition", () => {
  const profile =
    destinationAccessProfile({
      slug: "acacus",
    });

  assert.equal(
    profile.accessClass,
    "desert-expedition",
  );

  assert.equal(
    profile.requires4x4,
    true,
  );

  assert.equal(
    profile.requiresGuide,
    true,
  );
});


test("desert destination requires special access", () => {
  assert.equal(
    requiresSpecialAccess({
      slug: "desert",
    }),
    true,
  );
});


test("standard destination does not require special access", () => {
  assert.equal(
    requiresSpecialAccess({
      slug: "sabratha",
    }),
    false,
  );
});


test("unknown destination uses safe fallback profile", () => {
  const profile =
    destinationAccessProfile({
      slug: "unknown-place",
    });

  assert.equal(
    profile.accessClass,
    "unknown",
  );

  assert.equal(
    profile.roadFactor,
    1,
  );
});


test("road factor increases remote travel estimate", () => {
  const adjusted =
    adjustedRoadTravelMinutes(
      120,
      {
        slug: "awjila",
      },
    );

  assert.ok(
    adjusted > 120,
  );
});


test("standard road leaves estimated time unchanged", () => {
  assert.equal(
    adjustedRoadTravelMinutes(
      120,
      {
        slug: "tripoli",
      },
    ),
    120,
  );
});


test("invalid base travel time returns null", () => {
  assert.equal(
    adjustedRoadTravelMinutes(
      "invalid",
      {
        slug: "tripoli",
      },
    ),
    null,
  );
});


test("Acacus receives stronger road feasibility penalty", () => {
  assert.ok(
    roadFeasibilityPenalty({
      slug: "acacus",
    }) >
    roadFeasibilityPenalty({
      slug: "ghadames",
    }),
  );
});


test("road feasibility evidence is explainable", () => {
  const evidence =
    roadFeasibilityEvidence({
      slug: "acacus",
    });

  assert.equal(
    evidence.accessClass,
    "desert-expedition",
  );

  assert.equal(
    evidence.requires4x4,
    true,
  );

  assert.equal(
    evidence.requiresGuide,
    true,
  );

  assert.equal(
    evidence.penalty,
    25,
  );
});
