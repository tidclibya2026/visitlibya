import assert from "node:assert/strict";
import test from "node:test";

import {
  countOptimizedDestinations,
  optimizationChanged,
  optimizationEvidence,
  optimizationSummary,
  optimizeItineraryStructure,
  reduceHighIntensityDays,
  removeUnscheduledStops,
} from "../assets/js/app/ai/trip-auto-optimization.js";


const trip = {
  days: [
    {
      dayNumber: 1,

      summary: {
        intensity: "high",
        travelMinutes: 90,
      },

      destinations: [
        {
          slug: "tripoli",
          planner_score: {
            total: 90,
          },
        },
        {
          slug: "sabratha",
          planner_score: {
            total: 60,
          },
        },
        {
          slug: "leptis-magna",
          planner_score: {
            total: 80,
          },
        },
      ],

      timeline: [
        {
          type: "destination",
          scheduled: true,
          destination: {
            slug: "tripoli",
          },
        },
        {
          type: "destination",
          scheduled: false,
          destination: {
            slug: "sabratha",
          },
        },
        {
          type: "destination",
          scheduled: true,
          destination: {
            slug: "leptis-magna",
          },
        },
      ],
    },
  ],
};


test("optimization evidence detects overloaded day", () => {
  const evidence =
    optimizationEvidence(
      trip,
    );

  assert.deepEqual(
    evidence.overloadedDays,
    [1],
  );
});


test("optimization evidence detects unscheduled stop", () => {
  const evidence =
    optimizationEvidence(
      trip,
    );

  assert.equal(
    evidence.unscheduledStops[0]
      .slug,
    "sabratha",
  );
});


test("optimization evidence detects long travel day", () => {
  const evidence =
    optimizationEvidence({
      days: [
        {
          dayNumber: 2,

          summary: {
            travelMinutes: 400,
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


test("unscheduled destination is removed", () => {
  const result =
    removeUnscheduledStops(
      trip.days,
    );

  assert.equal(
    result[0].destinations.some(
      (destination) =>
        destination.slug ===
        "sabratha",
    ),
    false,
  );
});


test("scheduled destinations remain", () => {
  const result =
    removeUnscheduledStops(
      trip.days,
    );

  assert.ok(
    result[0].destinations.some(
      (destination) =>
        destination.slug ===
        "tripoli",
    ),
  );
});


test("high intensity day removes lowest scoring destination", () => {
  const result =
    reduceHighIntensityDays([
      {
        dayNumber: 1,

        summary: {
          intensity: "high",
        },

        destinations: [
          {
            slug: "a",
            planner_score: {
              total: 90,
            },
          },
          {
            slug: "b",
            planner_score: {
              total: 40,
            },
          },
        ],
      },
    ]);

  assert.deepEqual(
    result[0]
      .destinations
      .map(
        (destination) =>
          destination.slug,
      ),
    ["a"],
  );
});


test("normal intensity day is unchanged", () => {
  const days = [
    {
      summary: {
        intensity: "moderate",
      },

      destinations: [
        {
          slug: "a",
        },
        {
          slug: "b",
        },
      ],
    },
  ];

  const result =
    reduceHighIntensityDays(
      days,
    );

  assert.equal(
    result[0]
      .destinations.length,
    2,
  );
});


test("optimizer reports actions", () => {
  const result =
    optimizeItineraryStructure(
      trip,
    );

  assert.ok(
    result.actions.includes(
      "remove-unscheduled-stops",
    ),
  );

  assert.ok(
    result.actions.includes(
      "reduce-high-intensity-days",
    ),
  );
});


test("optimizer does not mutate original itinerary", () => {
  const before =
    JSON.stringify(
      trip,
    );

  optimizeItineraryStructure(
    trip,
  );

  assert.equal(
    JSON.stringify(trip),
    before,
  );
});


test("optimization changed is true when destinations change", () => {
  const result =
    optimizeItineraryStructure(
      trip,
    );

  assert.equal(
    optimizationChanged(
      result,
    ),
    true,
  );
});


test("destination counter counts optimized stops", () => {
  assert.equal(
    countOptimizedDestinations(
      trip.days,
    ),
    3,
  );
});


test("optimization summary reports removed destinations", () => {
  const result =
    optimizeItineraryStructure(
      trip,
    );

  const summary =
    optimizationSummary(
      result,
    );

  assert.ok(
    summary.removedDestinationCount >=
    1,
  );
});


test("balanced itinerary can remain unchanged", () => {
  const result =
    optimizeItineraryStructure({
      days: [
        {
          dayNumber: 1,

          summary: {
            intensity: "moderate",
            travelMinutes: 60,
          },

          timeline: [
            {
              type: "destination",
              scheduled: true,
              destination: {
                slug: "tripoli",
              },
            },
          ],

          destinations: [
            {
              slug: "tripoli",
              planner_score: {
                total: 80,
              },
            },
          ],
        },
      ],
    });

  assert.equal(
    optimizationChanged(
      result,
    ),
    false,
  );
});


test("invalid itinerary remains safe", () => {
  const result =
    optimizeItineraryStructure(
      null,
    );

  assert.deepEqual(
    result.originalDays,
    [],
  );

  assert.deepEqual(
    result.optimizedDays,
    [],
  );
});
