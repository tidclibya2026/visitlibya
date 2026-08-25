import assert from "node:assert/strict";
import test from "node:test";

import {
  createLunchStop,
  createShortRestStop,
  insertMealAndRestStops,
  lunchWindowStatus,
  mealRestRules,
  shouldInsertLunch,
  shouldInsertShortRest,
} from "../assets/js/app/ai/meal-rest-intelligence.js";


test("relaxed pace has longest lunch break", () => {
  assert.ok(
    mealRestRules("relaxed")
      .lunchDurationMinutes >
    mealRestRules("active")
      .lunchDurationMinutes,
  );
});


test("unknown pace falls back to balanced", () => {
  assert.deepEqual(
    mealRestRules("unknown"),
    mealRestRules("balanced"),
  );
});


test("short rest is inserted after activity threshold", () => {
  assert.equal(
    shouldInsertShortRest({
      continuousActivityMinutes: 180,
      pace: "balanced",
    }),
    true,
  );
});


test("short rest is not inserted too early", () => {
  assert.equal(
    shouldInsertShortRest({
      continuousActivityMinutes: 120,
      pace: "balanced",
    }),
    false,
  );
});


test("lunch window is detected correctly", () => {
  assert.equal(
    lunchWindowStatus(
      12 * 60,
      "balanced",
    ),
    "before",
  );

  assert.equal(
    lunchWindowStatus(
      13 * 60,
      "balanced",
    ),
    "within",
  );

  assert.equal(
    lunchWindowStatus(
      15 * 60,
      "balanced",
    ),
    "after",
  );
});


test("lunch is inserted only once", () => {
  assert.equal(
    shouldInsertLunch({
      currentMinutes:
        13 * 60,
      lunchInserted: false,
      pace: "balanced",
    }),
    true,
  );

  assert.equal(
    shouldInsertLunch({
      currentMinutes:
        13 * 60,
      lunchInserted: true,
      pace: "balanced",
    }),
    false,
  );
});


test("short rest stop has expected duration", () => {
  const stop =
    createShortRestStop({
      startsAt: 660,
      pace: "balanced",
    });

  assert.equal(
    stop.type,
    "rest",
  );

  assert.equal(
    stop.durationMinutes,
    20,
  );

  assert.equal(
    stop.endsAt,
    680,
  );
});


test("lunch stop has expected duration", () => {
  const stop =
    createLunchStop({
      startsAt: 780,
      pace: "balanced",
    });

  assert.equal(
    stop.type,
    "meal",
  );

  assert.equal(
    stop.mealType,
    "lunch",
  );

  assert.equal(
    stop.durationMinutes,
    60,
  );
});


test("sequence inserts lunch around midday", () => {
  const result =
    insertMealAndRestStops({
      pace: "balanced",
      scheduledItems: [
        {
          destination: {
            slug: "first",
          },
          scheduled: true,
          startsAt: 540,
          endsAt: 660,
        },
        {
          destination: {
            slug: "second",
          },
          scheduled: true,
          startsAt: 780,
          endsAt: 900,
        },
      ],
    });

  assert.ok(
    result.some(
      (item) =>
        item?.type ===
          "meal" &&
        item?.mealType ===
          "lunch",
    ),
  );
});


test("sequence keeps destination items", () => {
  const destination = {
    destination: {
      slug: "first",
    },
    scheduled: true,
    startsAt: 540,
    endsAt: 660,
  };

  const result =
    insertMealAndRestStops({
      scheduledItems: [
        destination,
      ],
      pace: "balanced",
    });

  assert.ok(
    result.includes(
      destination,
    ),
  );
});
