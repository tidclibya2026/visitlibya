import assert from "node:assert/strict";
import test from "node:test";

import {
  feasibilityMessages,
  feasibilityPenalty,
  feasibilityRating,
  itineraryEvidence,
  tripFeasibility,
} from "../assets/js/app/ai/trip-feasibility-score.js";


const healthyItinerary = {
  days: [
    {
      summary: {
        intensity: "moderate",
        travelMinutes: 60,
        visitMinutes: 300,
        recoveryMinutes: 60,
      },
      timeline: [
        {
          type: "destination",
          scheduled: true,
          conflictAdjusted: false,
        },
      ],
      destinations: [
        {
          planner_score: {
            requires4x4: false,
            requiresGuide: false,
          },
        },
      ],
    },
  ],
};


test("itinerary evidence counts days", () => {
  const evidence =
    itineraryEvidence(
      healthyItinerary,
    );

  assert.equal(
    evidence.dayCount,
    1,
  );
});


test("itinerary evidence counts destinations", () => {
  const evidence =
    itineraryEvidence(
      healthyItinerary,
    );

  assert.equal(
    evidence.destinationCount,
    1,
  );
});


test("healthy itinerary has no unscheduled stops", () => {
  const evidence =
    itineraryEvidence(
      healthyItinerary,
    );

  assert.equal(
    evidence.unscheduledStops,
    0,
  );
});


test("high intensity day is detected", () => {
  const evidence =
    itineraryEvidence({
      days: [
        {
          summary: {
            intensity: "high",
          },
          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.equal(
    evidence.highIntensityDays,
    1,
  );
});


test("long travel day is detected", () => {
  const evidence =
    itineraryEvidence({
      days: [
        {
          summary: {
            travelMinutes: 400,
          },
          timeline: [],
          destinations: [],
        },
      ],
    });

  assert.equal(
    evidence.longTravelDays,
    1,
  );
});


test("special access destination is detected", () => {
  const evidence =
    itineraryEvidence({
      days: [
        {
          summary: {},
          timeline: [],
          destinations: [
            {
              planner_score: {
                requires4x4: true,
              },
            },
          ],
        },
      ],
    });

  assert.equal(
    evidence.specialAccessStops,
    1,
  );
});


test("unscheduled stop applies strong penalty", () => {
  const penalty =
    feasibilityPenalty({
      unscheduledStops: 1,
      dayCount: 1,
      totalRecoveryMinutes: 60,
    });

  assert.ok(
    penalty >= 18,
  );
});


test("high intensity applies penalty", () => {
  const penalty =
    feasibilityPenalty({
      highIntensityDays: 1,
      dayCount: 1,
      totalRecoveryMinutes: 60,
    });

  assert.ok(
    penalty >= 8,
  );
});


test("travel heavier than visits applies penalty", () => {
  const penalty =
    feasibilityPenalty({
      totalTravelMinutes: 500,
      totalVisitMinutes: 300,
      totalRecoveryMinutes: 60,
      dayCount: 1,
    });

  assert.ok(
    penalty >= 8,
  );
});


test("excellent rating starts at ninety", () => {
  assert.equal(
    feasibilityRating(90),
    "excellent",
  );
});


test("good rating starts at seventy five", () => {
  assert.equal(
    feasibilityRating(75),
    "good",
  );
});


test("fair rating starts at sixty", () => {
  assert.equal(
    feasibilityRating(60),
    "fair",
  );
});


test("low score requires review", () => {
  assert.equal(
    feasibilityRating(40),
    "needs-review",
  );
});


test("healthy itinerary exposes strengths", () => {
  const messages =
    feasibilityMessages(
      itineraryEvidence(
        healthyItinerary,
      ),
    );

  assert.ok(
    messages.strengths.includes(
      "all-stops-scheduled",
    ),
  );

  assert.ok(
    messages.strengths.includes(
      "no-timeline-conflicts",
    ),
  );
});


test("trip feasibility returns score and rating", () => {
  const result =
    tripFeasibility(
      healthyItinerary,
    );

  assert.equal(
    typeof result.score,
    "number",
  );

  assert.ok(
    result.score >= 0 &&
    result.score <= 100,
  );

  assert.ok(
    [
      "excellent",
      "good",
      "fair",
      "needs-review",
    ].includes(
      result.rating,
    ),
  );
});


test("empty itinerary remains safe", () => {
  const result =
    tripFeasibility({
      days: [],
    });

  assert.equal(
    result.evidence.dayCount,
    0,
  );

  assert.equal(
    typeof result.score,
    "number",
  );
});
