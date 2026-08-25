import assert from "node:assert/strict";
import test from "node:test";

import {
  orderDestinationsWithinRegion,
  routePosition,
} from "../assets/js/app/ai/route-sequencing.js";


test("east route starts from Benghazi", () => {
  assert.equal(
    routePosition(
      { slug: "benghazi" },
      "east",
    ),
    0,
  );
});


test("east destinations follow tourism corridor order", () => {
  const ordered =
    orderDestinationsWithinRegion(
      [
        { slug: "bomba-bay" },
        { slug: "benghazi" },
        { slug: "green-mountain" },
      ],
      "east",
    );

  assert.deepEqual(
    ordered.map((item) => item.slug),
    [
      "benghazi",
      "green-mountain",
      "bomba-bay",
    ],
  );
});


test("northwest destinations follow corridor order", () => {
  const ordered =
    orderDestinationsWithinRegion(
      [
        { slug: "nafusa" },
        { slug: "tripoli" },
        { slug: "sabratha" },
        { slug: "leptis-magna" },
      ],
      "northwest",
    );

  assert.deepEqual(
    ordered.map((item) => item.slug),
    [
      "tripoli",
      "leptis-magna",
      "sabratha",
      "nafusa",
    ],
  );
});


test("unknown destinations are placed after known route stops", () => {
  const ordered =
    orderDestinationsWithinRegion(
      [
        { slug: "unknown-place" },
        { slug: "benghazi" },
      ],
      "east",
    );

  assert.deepEqual(
    ordered.map((item) => item.slug),
    [
      "benghazi",
      "unknown-place",
    ],
  );
});
