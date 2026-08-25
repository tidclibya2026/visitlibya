import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveTimelineConflicts,
  shiftTimelineItem,
  timelineHasConflict,
  timelineIsConflictFree,
  timelineItemDuration,
} from "../assets/js/app/ai/timeline-conflict-resolution.js";


test("timeline duration uses explicit duration", () => {
  assert.equal(
    timelineItemDuration({
      durationMinutes: 60,
      startsAt: 500,
      endsAt: 700,
    }),
    60,
  );
});


test("timeline duration can be derived from times", () => {
  assert.equal(
    timelineItemDuration({
      startsAt: 540,
      endsAt: 660,
    }),
    120,
  );
});


test("timeline conflict is detected", () => {
  assert.equal(
    timelineHasConflict(
      {
        startsAt: 540,
        endsAt: 660,
      },
      {
        startsAt: 630,
        endsAt: 750,
      },
    ),
    true,
  );
});


test("adjacent items do not conflict", () => {
  assert.equal(
    timelineHasConflict(
      {
        startsAt: 540,
        endsAt: 660,
      },
      {
        startsAt: 660,
        endsAt: 720,
      },
    ),
    false,
  );
});


test("timeline item can be shifted", () => {
  const result =
    shiftTimelineItem(
      {
        type: "meal",
        startsAt: 600,
        endsAt: 660,
      },
      720,
    );

  assert.equal(
    result.startsAt,
    720,
  );

  assert.equal(
    result.endsAt,
    780,
  );

  assert.equal(
    result.conflictAdjusted,
    true,
  );
});


test("conflicting item is moved after previous item", () => {
  const result =
    resolveTimelineConflicts([
      {
        type: "destination",
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "travel",
        startsAt: 600,
        endsAt: 660,
      },
    ]);

  assert.equal(
    result[1].startsAt,
    660,
  );

  assert.equal(
    result[1].endsAt,
    720,
  );
});


test("conflict resolution preserves item order", () => {
  const result =
    resolveTimelineConflicts([
      {
        type: "destination",
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "meal",
        startsAt: 630,
        endsAt: 690,
      },
      {
        type: "destination",
        startsAt: 660,
        endsAt: 780,
      },
    ]);

  assert.deepEqual(
    result.map(
      (item) => item.type,
    ),
    [
      "destination",
      "meal",
      "destination",
    ],
  );
});


test("resolved timeline is conflict free", () => {
  const result =
    resolveTimelineConflicts([
      {
        type: "destination",
        startsAt: 540,
        endsAt: 660,
      },
      {
        type: "meal",
        startsAt: 620,
        endsAt: 680,
      },
      {
        type: "rest",
        startsAt: 650,
        endsAt: 670,
      },
    ]);

  assert.equal(
    timelineIsConflictFree(
      result,
    ),
    true,
  );
});


test("already valid timeline remains conflict free", () => {
  const result =
    resolveTimelineConflicts([
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
    ]);

  assert.equal(
    timelineIsConflictFree(
      result,
    ),
    true,
  );

  assert.equal(
    result.every(
      (item) =>
        item.conflictAdjusted ===
        false,
    ),
    true,
  );
});


test("invalid timeline input returns empty array", () => {
  assert.deepEqual(
    resolveTimelineConflicts(
      null,
    ),
    [],
  );
});
