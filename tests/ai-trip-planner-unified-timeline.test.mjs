import assert from "node:assert/strict";
import test from "node:test";

import {
  buildTravelTimelineItem,
  insertTravelBetweenDestinations,
  sortTimelineItems,
  unifiedDailyTimeline,
} from "../assets/js/app/ai/unified-daily-timeline.js";


const tripoli = {
  slug: "tripoli",
  latitude: 32.8872,
  longitude: 13.1913,
};

const sabratha = {
  slug: "sabratha",
  latitude: 32.7933,
  longitude: 12.4885,
};


test("travel timeline item is built from coordinates", () => {
  const item =
    buildTravelTimelineItem({
      previousDestination:
        tripoli,

      nextDestination:
        sabratha,

      startsAt: 720,
    });

  assert.equal(
    item.type,
    "travel",
  );

  assert.ok(
    item.durationMinutes > 0,
  );

  assert.equal(
    item.startsAt,
    720,
  );

  assert.ok(
    item.endsAt > 720,
  );
});


test("travel timeline item requires destinations", () => {
  assert.equal(
    buildTravelTimelineItem({
      previousDestination: null,
      nextDestination: sabratha,
      startsAt: 720,
    }),
    null,
  );
});


test("timeline sorting is chronological", () => {
  const result =
    sortTimelineItems([
      {
        type: "destination",
        startsAt: 780,
        endsAt: 900,
      },
      {
        type: "meal",
        startsAt: 720,
        endsAt: 780,
      },
    ]);

  assert.equal(
    result[0].type,
    "meal",
  );

  assert.equal(
    result[1].type,
    "destination",
  );
});


test("travel is inserted between scheduled destinations", () => {
  const result =
    insertTravelBetweenDestinations([
      {
        type: "destination",
        destination:
          tripoli,
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "destination",
        destination:
          sabratha,
        startsAt: 780,
        endsAt: 900,
      },
    ]);

  assert.equal(
    result.filter(
      (item) =>
        item.type ===
        "travel",
    ).length,
    1,
  );
});


test("meal and rest items are preserved", () => {
  const result =
    insertTravelBetweenDestinations([
      {
        type: "destination",
        destination:
          tripoli,
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "meal",
        startsAt: 660,
        endsAt: 720,
      },
      {
        type: "rest",
        startsAt: 720,
        endsAt: 740,
      },
    ]);

  assert.ok(
    result.some(
      (item) =>
        item.type === "meal",
    ),
  );

  assert.ok(
    result.some(
      (item) =>
        item.type === "rest",
    ),
  );
});


test("unified timeline exposes formatted labels", () => {
  const result =
    unifiedDailyTimeline([
      {
        type: "destination",
        destination:
          tripoli,
        startsAt: 540,
        endsAt: 660,
      },
    ]);

  assert.equal(
    result[0].startsAtLabel,
    "09:00",
  );

  assert.equal(
    result[0].endsAtLabel,
    "11:00",
  );
});


test("invalid timeline input returns empty array", () => {
  assert.deepEqual(
    unifiedDailyTimeline(null),
    [],
  );
});


test("travel timeline preserves route endpoints", () => {
  const item =
    buildTravelTimelineItem({
      previousDestination:
        tripoli,

      nextDestination:
        sabratha,

      startsAt: 600,
    });

  assert.equal(
    item.fromDestination.slug,
    "tripoli",
  );

  assert.equal(
    item.toDestination.slug,
    "sabratha",
  );
});

test("unified timeline resolves overlapping travel and destination times", () => {
  const result =
    unifiedDailyTimeline([
      {
        type: "destination",
        destination:
          tripoli,
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "destination",
        destination:
          sabratha,
        startsAt: 660,
        endsAt: 780,
      },
    ]);

  for (
    let index = 1;
    index < result.length;
    index += 1
  ) {
    const previous =
      result[index - 1];

    const current =
      result[index];

    if (
      Number.isFinite(previous.endsAt) &&
      Number.isFinite(current.startsAt)
    ) {
      assert.ok(
        current.startsAt >=
        previous.endsAt,
      );
    }
  }
});


test("unified timeline marks shifted conflicting items", () => {
  const result =
    unifiedDailyTimeline([
      {
        type: "destination",
        destination:
          tripoli,
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "meal",
        startsAt: 630,
        endsAt: 690,
      },
    ]);

  const meal =
    result.find(
      (item) =>
        item.type === "meal",
    );

  assert.equal(
    meal.conflictAdjusted,
    true,
  );

  assert.equal(
    meal.startsAt,
    660,
  );
});
