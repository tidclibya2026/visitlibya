import assert from "node:assert/strict";
import test from "node:test";

import {
  dailyTravelBudgetMinutes,
  estimatedTravelMinutes,
  requiresTravelTimeDay,
  travelTimeBand,
  travelTimePenalty,
} from "../assets/js/app/ai/travel-time-intelligence.js";


const tripoli = {
  latitude: 32.8872,
  longitude: 13.1913,
};

const benghazi = {
  latitude: 32.1167,
  longitude: 20.0667,
};


test("same point has zero estimated travel time", () => {
  assert.equal(
    estimatedTravelMinutes(
      tripoli,
      tripoli,
    ),
    0,
  );
});


test("Tripoli to Benghazi has long estimated travel time", () => {
  const minutes =
    estimatedTravelMinutes(
      tripoli,
      benghazi,
    );

  assert.ok(minutes > 500);
});


test("relaxed pace has smallest daily travel budget", () => {
  assert.equal(
    dailyTravelBudgetMinutes(
      "relaxed",
    ),
    180,
  );

  assert.equal(
    dailyTravelBudgetMinutes(
      "balanced",
    ),
    300,
  );

  assert.equal(
    dailyTravelBudgetMinutes(
      "active",
    ),
    450,
  );
});


test("unknown pace falls back to balanced", () => {
  assert.equal(
    dailyTravelBudgetMinutes(
      "unknown",
    ),
    300,
  );
});


test("travel time bands are classified correctly", () => {
  assert.equal(
    travelTimeBand(60),
    "short",
  );

  assert.equal(
    travelTimeBand(150),
    "moderate",
  );

  assert.equal(
    travelTimeBand(300),
    "long",
  );

  assert.equal(
    travelTimeBand(500),
    "very-long",
  );
});


test("short trip heavily penalizes very long travel", () => {
  const result =
    travelTimePenalty({
      source: tripoli,
      target: benghazi,
      pace: "balanced",
      days: 3,
    });

  assert.equal(
    result.band,
    "very-long",
  );

  assert.ok(
    result.penalty >= 90,
  );
});


test("longer trip reduces very long travel penalty", () => {
  const shortTrip =
    travelTimePenalty({
      source: tripoli,
      target: benghazi,
      pace: "balanced",
      days: 3,
    });

  const longTrip =
    travelTimePenalty({
      source: tripoli,
      target: benghazi,
      pace: "balanced",
      days: 8,
    });

  assert.ok(
    longTrip.penalty <
    shortTrip.penalty,
  );
});


test("Tripoli to Benghazi exceeds relaxed daily travel budget", () => {
  assert.equal(
    requiresTravelTimeDay({
      source: tripoli,
      target: benghazi,
      pace: "relaxed",
    }),
    true,
  );
});


test("same point does not require travel day", () => {
  assert.equal(
    requiresTravelTimeDay({
      source: tripoli,
      target: tripoli,
      pace: "relaxed",
    }),
    false,
  );
});
