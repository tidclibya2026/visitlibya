import assert from "node:assert/strict";
import test from "node:test";

import {
  canScheduleVisit,
  defaultDayWindow,
  destinationOpeningWindow,
  formatClockMinutes,
  parseClockMinutes,
  scheduleDestinationSequence,
} from "../assets/js/app/ai/opening-hours-intelligence.js";


test("clock parser converts HH:MM to minutes", () => {
  assert.equal(
    parseClockMinutes("09:30"),
    570,
  );
});


test("invalid clock value is rejected", () => {
  assert.equal(
    parseClockMinutes("25:00"),
    null,
  );

  assert.equal(
    parseClockMinutes("9:30"),
    null,
  );
});


test("clock formatter converts minutes to HH:MM", () => {
  assert.equal(
    formatClockMinutes(570),
    "09:30",
  );
});


test("destination exposes known opening window", () => {
  const result =
    destinationOpeningWindow({
      opening_time: "09:00",
      closing_time: "17:00",
    });

  assert.equal(
    result.status,
    "known",
  );

  assert.equal(
    result.opensAt,
    540,
  );

  assert.equal(
    result.closesAt,
    1020,
  );
});


test("missing opening hours remain unknown", () => {
  const result =
    destinationOpeningWindow({
      slug: "unknown-site",
    });

  assert.equal(
    result.status,
    "unknown",
  );
});


test("unknown opening hours do not block visit", () => {
  const result =
    canScheduleVisit({
      destination: {
        slug: "unknown-site",
      },
      arrivalMinutes: 600,
      visitMinutes: 120,
    });

  assert.equal(
    result.schedulable,
    true,
  );

  assert.equal(
    result.reason,
    "opening-hours-unknown",
  );
});


test("planner waits until attraction opens", () => {
  const result =
    canScheduleVisit({
      destination: {
        opening_time: "10:00",
        closing_time: "18:00",
      },
      arrivalMinutes: 540,
      visitMinutes: 120,
    });

  assert.equal(
    result.schedulable,
    true,
  );

  assert.equal(
    result.startsAt,
    600,
  );

  assert.equal(
    result.endsAt,
    720,
  );
});


test("visit is rejected when closing time is insufficient", () => {
  const result =
    canScheduleVisit({
      destination: {
        opening_time: "09:00",
        closing_time: "12:00",
      },
      arrivalMinutes: 660,
      visitMinutes: 120,
    });

  assert.equal(
    result.schedulable,
    false,
  );

  assert.equal(
    result.reason,
    "insufficient-opening-window",
  );
});


test("daily start time varies by pace", () => {
  assert.equal(
    defaultDayWindow("relaxed")
      .startsAt,
    600,
  );

  assert.equal(
    defaultDayWindow("balanced")
      .startsAt,
    540,
  );

  assert.equal(
    defaultDayWindow("active")
      .startsAt,
    480,
  );
});


test("sequence schedules visits chronologically", () => {
  const result =
    scheduleDestinationSequence({
      destinations: [
        {
          slug: "first",
          opening_time: "09:00",
          closing_time: "18:00",
        },
        {
          slug: "second",
          opening_time: "09:00",
          closing_time: "18:00",
        },
      ],
      pace: "balanced",
      visitDurationResolver:
        () => 120,
    });

  assert.equal(
    result[0].startsAt,
    540,
  );

  assert.equal(
    result[0].endsAt,
    660,
  );

  assert.equal(
    result[1].startsAt,
    660,
  );

  assert.equal(
    result[1].endsAt,
    780,
  );
});


test("sequence rejects visit outside daily window", () => {
  const result =
    scheduleDestinationSequence({
      destinations: [
        {
          slug: "one",
        },
        {
          slug: "two",
        },
        {
          slug: "three",
        },
        {
          slug: "four",
        },
      ],
      pace: "relaxed",
      visitDurationResolver:
        () => 180,
    });

  assert.equal(
    result[0].scheduled,
    true,
  );

  assert.equal(
    result[1].scheduled,
    true,
  );

  assert.equal(
    result[2].scheduled,
    false,
  );
});
