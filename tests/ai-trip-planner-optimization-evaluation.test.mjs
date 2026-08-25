import assert from "node:assert/strict";
import test from "node:test";

import {
  evaluateOptimization,
  rebuildOptimizedDays,
  rebuildOptimizedVisitDay,
} from "../assets/js/app/ai/trip-optimization-evaluation.js";


const tripoli = {
  slug: "tripoli",
  category_key: "historic-cities",
  latitude: 32.8872,
  longitude: 13.1913,

  planner_score: {
    total: 90,
  },
};


const sabratha = {
  slug: "sabratha",
  category_key: "archaeological-sites",
  latitude: 32.7933,
  longitude: 12.4885,

  planner_score: {
    total: 70,
  },
};


test("optimized visit day rebuilds visit budget", () => {
  const result =
    rebuildOptimizedVisitDay(
      {
        dayNumber: 1,
        type: "visit",

        destinations: [
          tripoli,
        ],
      },
      {
        pace: "balanced",
      },
    );

  assert.ok(
    result.visitBudget,
  );

  assert.equal(
    typeof result.visitBudget
      .usedMinutes,
    "number",
  );
});


test("optimized visit day rebuilds schedule", () => {
  const result =
    rebuildOptimizedVisitDay(
      {
        dayNumber: 1,
        type: "visit",

        destinations: [
          tripoli,
        ],
      },
      {
        pace: "balanced",
      },
    );

  assert.equal(
    typeof result.destinations[0]
      .planner_score.scheduled,
    "boolean",
  );
});


test("optimized visit day rebuilds timeline", () => {
  const result =
    rebuildOptimizedVisitDay(
      {
        dayNumber: 1,
        type: "visit",

        destinations: [
          tripoli,
          sabratha,
        ],
      },
      {
        pace: "balanced",
      },
    );

  assert.ok(
    Array.isArray(
      result.timeline,
    ),
  );

  assert.ok(
    result.timeline.some(
      (item) =>
        item.type ===
        "destination",
    ),
  );
});


test("optimized visit day rebuilds daily summary", () => {
  const result =
    rebuildOptimizedVisitDay(
      {
        dayNumber: 1,
        type: "visit",

        destinations: [
          tripoli,
        ],
      },
      {
        pace: "balanced",
      },
    );

  assert.ok(
    result.summary,
  );

  assert.equal(
    typeof result.summary
      .visitMinutes,
    "number",
  );
});


test("rebuild optimized days preserves travel days", () => {
  const result =
    rebuildOptimizedDays(
      [
        {
          dayNumber: 1,
          type: "travel",
          fromRegion: "east",
          toRegion: "southwest",
          destinations: [],
        },
      ],
      {
        pace: "balanced",
      },
    );

  assert.equal(
    result[0].type,
    "travel",
  );

  assert.equal(
    result[0]
      .destinations.length,
    0,
  );
});


test("optimization evaluation exposes before feasibility", () => {
  const result =
    evaluateOptimization({
      originalDays: [
        {
          dayNumber: 1,
          type: "visit",

          destinations: [
            tripoli,
          ],

          timeline: [],
          summary: {
            intensity: "moderate",
            travelMinutes: 0,
            visitMinutes: 120,
            recoveryMinutes: 60,
          },
        },
      ],

      optimizedDays: [
        {
          dayNumber: 1,
          type: "visit",

          destinations: [
            tripoli,
          ],
        },
      ],

      preferences: {
        pace: "balanced",
      },
    });

  assert.equal(
    typeof result.before
      .feasibility.score,
    "number",
  );
});


test("optimization evaluation exposes after feasibility", () => {
  const result =
    evaluateOptimization({
      originalDays: [],

      optimizedDays: [
        {
          dayNumber: 1,
          type: "visit",

          destinations: [
            tripoli,
          ],
        },
      ],

      preferences: {
        pace: "balanced",
      },
    });

  assert.equal(
    typeof result.after
      .feasibility.score,
    "number",
  );
});


test("optimization evaluation exposes score delta", () => {
  const result =
    evaluateOptimization({
      originalDays: [],
      optimizedDays: [],

      preferences: {
        pace: "balanced",
      },
    });

  assert.equal(
    typeof result.improvement
      .scoreDelta,
    "number",
  );
});


test("optimization evaluation exposes destination counts", () => {
  const result =
    evaluateOptimization({
      originalDays: [
        {
          destinations: [
            tripoli,
            sabratha,
          ],
        },
      ],

      optimizedDays: [
        {
          destinations: [
            tripoli,
          ],
        },
      ],

      preferences: {
        pace: "balanced",
      },
    });

  assert.equal(
    result.before
      .destinationCount,
    2,
  );

  assert.equal(
    result.after
      .destinationCount,
    1,
  );
});


test("optimization evaluation remains safe with empty input", () => {
  const result =
    evaluateOptimization();

  assert.deepEqual(
    result.before.days,
    [],
  );

  assert.deepEqual(
    result.after.days,
    [],
  );
});
