import assert from "node:assert/strict";
import test from "node:test";

import {
  dailyStopCount,
  dailySummary,
  dayIntensity,
} from "../assets/js/app/ai/daily-summary-intelligence.js";


const timeline = [
  {
    type: "destination",
    startsAt: 540,
    endsAt: 660,
  },
  {
    type: "travel",
    startsAt: 660,
    endsAt: 720,
  },
  {
    type: "meal",
    startsAt: 720,
    endsAt: 780,
  },
  {
    type: "destination",
    startsAt: 780,
    endsAt: 900,
  },
  {
    type: "rest",
    startsAt: 900,
    endsAt: 920,
  },
];


test("daily stop count includes destinations only", () => {
  assert.equal(
    dailyStopCount(
      timeline,
    ),
    2,
  );
});


test("daily summary calculates visit minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.visitMinutes,
    240,
  );
});


test("daily summary calculates travel minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.travelMinutes,
    60,
  );
});


test("daily summary calculates meal minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.mealMinutes,
    60,
  );
});


test("daily summary calculates rest minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.restMinutes,
    20,
  );
});


test("daily summary exposes first start time", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.startsAt,
    540,
  );
});


test("daily summary exposes last end time", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.endsAt,
    920,
  );
});


test("daily summary calculates total day duration", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.totalDayMinutes,
    380,
  );
});


test("daily summary calculates activity minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.activityMinutes,
    300,
  );
});


test("daily summary calculates recovery minutes", () => {
  const summary =
    dailySummary(
      timeline,
    );

  assert.equal(
    summary.recoveryMinutes,
    80,
  );
});


test("empty timeline returns safe summary", () => {
  assert.deepEqual(
    dailySummary([]),
    {
      stopCount: 0,
      visitMinutes: 0,
      travelMinutes: 0,
      mealMinutes: 0,
      restMinutes: 0,
      startsAt: null,
      endsAt: null,
      totalDayMinutes: 0,
      activityMinutes: 0,
      recoveryMinutes: 0,
    },
  );
});


test("day intensity can be light", () => {
  assert.equal(
    dayIntensity({
      activityMinutes: 240,
      recoveryMinutes: 60,
      totalDayMinutes: 360,
    }),
    "light",
  );
});


test("day intensity can be moderate", () => {
  assert.equal(
    dayIntensity({
      activityMinutes: 360,
      recoveryMinutes: 60,
      totalDayMinutes: 480,
    }),
    "moderate",
  );
});


test("day intensity can be high", () => {
  assert.equal(
    dayIntensity({
      activityMinutes: 500,
      recoveryMinutes: 30,
      totalDayMinutes: 540,
    }),
    "high",
  );
});


test("day intensity is unknown without duration", () => {
  assert.equal(
    dayIntensity({
      activityMinutes: 0,
      recoveryMinutes: 0,
      totalDayMinutes: 0,
    }),
    "unknown",
  );
});
