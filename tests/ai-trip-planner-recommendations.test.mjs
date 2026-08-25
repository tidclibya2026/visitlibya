import assert from "node:assert/strict";
import test from "node:test";

import {
  buildTripRecommendations,
  recommendationPriorityRank,
  sortTripRecommendations,
  tripRecommendationEvidence,
} from "../assets/js/app/ai/trip-recommendation-insights.js";


const balancedTrip = {
  feasibility: {
    score: 92,
    rating: "excellent",
  },

  days: [
    {
      dayNumber: 1,

      summary: {
        intensity: "moderate",
        travelMinutes: 60,
        recoveryMinutes: 60,
      },

      timeline: [
        {
          type: "destination",
          scheduled: true,
        },
      ],

      destinations: [
        {
          slug: "tripoli",

          planner_score: {
            requires4x4: false,
            requiresGuide: false,
          },
        },
      ],
    },
  ],
};


test("recommendation evidence exposes feasibility score", () => {
  const evidence =
    tripRecommendationEvidence(
      balancedTrip,
    );

  assert.equal(
    evidence.feasibilityScore,
    92,
  );
});


test("high intensity day is collected", () => {
  const evidence =
    tripRecommendationEvidence({
      feasibility: {
        score: 70,
      },

      days: [
        {
          dayNumber: 2,

          summary: {
            intensity: "high",
            activityMinutes: 500,
            recoveryMinutes: 20,
          },

          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.equal(
    evidence.highIntensityDays.length,
    1,
  );

  assert.equal(
    evidence.highIntensityDays[0]
      .dayNumber,
    2,
  );
});


test("long travel day is collected", () => {
  const evidence =
    tripRecommendationEvidence({
      feasibility: {
        score: 75,
      },

      days: [
        {
          dayNumber: 3,

          summary: {
            travelMinutes: 420,
          },

          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.equal(
    evidence.longTravelDays.length,
    1,
  );
});


test("unscheduled stop is collected", () => {
  const evidence =
    tripRecommendationEvidence({
      feasibility: {
        score: 60,
      },

      days: [
        {
          dayNumber: 1,

          summary: {},

          timeline: [
            {
              type: "destination",
              scheduled: false,

              destination: {
                slug: "sabratha",
              },
            },
          ],

          destinations: [],
        },
      ],
    });

  assert.equal(
    evidence.unscheduledStops.length,
    1,
  );

  assert.equal(
    evidence.unscheduledStops[0]
      .slug,
    "sabratha",
  );
});


test("special access destination is collected", () => {
  const evidence =
    tripRecommendationEvidence({
      feasibility: {
        score: 80,
      },

      days: [
        {
          dayNumber: 1,
          summary: {},
          timeline: [],

          destinations: [
            {
              slug: "acacus",

              planner_score: {
                requires4x4: true,
                requiresGuide: true,
              },
            },
          ],
        },
      ],
    });

  assert.equal(
    evidence.specialAccessStops.length,
    1,
  );
});


test("unscheduled stop creates high priority recommendation", () => {
  const result =
    buildTripRecommendations({
      feasibility: {
        score: 60,
      },

      days: [
        {
          dayNumber: 1,
          summary: {
            recoveryMinutes: 60,
          },

          timeline: [
            {
              type: "destination",
              scheduled: false,
            },
          ],

          destinations: [],
        },
      ],
    });

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
          "review-unscheduled-stops" &&
        item.priority === "high",
    ),
  );
});


test("long travel creates separation recommendation", () => {
  const result =
    buildTripRecommendations({
      feasibility: {
        score: 70,
      },

      days: [
        {
          dayNumber: 1,

          summary: {
            travelMinutes: 400,
            recoveryMinutes: 60,
          },

          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
        "separate-long-travel",
    ),
  );
});


test("high intensity creates reduction recommendation", () => {
  const result =
    buildTripRecommendations({
      feasibility: {
        score: 75,
      },

      days: [
        {
          dayNumber: 1,

          summary: {
            intensity: "high",
            recoveryMinutes: 60,
          },

          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
        "reduce-day-intensity",
    ),
  );
});


test("low recovery creates recovery recommendation", () => {
  const result =
    buildTripRecommendations({
      feasibility: {
        score: 80,
      },

      days: [
        {
          dayNumber: 1,

          summary: {
            recoveryMinutes: 10,
          },

          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
        "increase-recovery-time",
    ),
  );
});


test("special access creates preparation recommendation", () => {
  const result =
    buildTripRecommendations({
      feasibility: {
        score: 80,
      },

      days: [
        {
          dayNumber: 1,

          summary: {
            recoveryMinutes: 60,
          },

          timeline: [],

          destinations: [
            {
              slug: "acacus",

              planner_score: {
                requires4x4: true,
              },
            },
          ],
        },
      ],
    });

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
        "prepare-special-access",
    ),
  );
});


test("excellent balanced trip receives positive insight", () => {
  const result =
    buildTripRecommendations(
      balancedTrip,
    );

  assert.ok(
    result.recommendations.some(
      (item) =>
        item.code ===
        "itinerary-well-balanced",
    ),
  );
});


test("high priority ranks before medium", () => {
  assert.ok(
    recommendationPriorityRank(
      "high",
    ) <
    recommendationPriorityRank(
      "medium",
    ),
  );
});


test("recommendations sort by priority", () => {
  const result =
    sortTripRecommendations([
      {
        code: "info",
        priority: "info",
      },
      {
        code: "high",
        priority: "high",
      },
      {
        code: "medium",
        priority: "medium",
      },
    ]);

  assert.deepEqual(
    result.map(
      (item) =>
        item.priority,
    ),
    [
      "high",
      "medium",
      "info",
    ],
  );
});


test("invalid recommendation list returns empty array", () => {
  assert.deepEqual(
    sortTripRecommendations(
      null,
    ),
    [],
  );
});
