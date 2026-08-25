import assert from "node:assert/strict";
import test from "node:test";

import {
  buildTravelAwareSequence,
  requiresTravelDay,
} from "../assets/js/app/ai/travel-day-planner.js";


test("same region does not require travel day", () => {
  assert.equal(
    requiresTravelDay(
      { slug: "benghazi" },
      { slug: "green-mountain" },
    ),
    false,
  );
});


test("east to western desert requires travel day", () => {
  assert.equal(
    requiresTravelDay(
      { slug: "benghazi" },
      { slug: "ghadames" },
    ),
    true,
  );
});


test("travel sequence inserts transition between distant regions", () => {
  const sequence =
    buildTravelAwareSequence([
      { slug: "benghazi" },
      { slug: "green-mountain" },
      { slug: "ghadames" },
    ]);

  assert.deepEqual(
    sequence.map((item) => item.type),
    [
      "destination",
      "destination",
      "travel",
      "destination",
    ],
  );
});


test("local eastern route has no travel transition", () => {
  const sequence =
    buildTravelAwareSequence([
      { slug: "benghazi" },
      { slug: "green-mountain" },
      { slug: "bomba-bay" },
    ]);

  assert.deepEqual(
    sequence.map((item) => item.type),
    [
      "destination",
      "destination",
      "destination",
    ],
  );
});
