import assert from "node:assert/strict";
import test from "node:test";

import {
  destinationRegion,
  geographicPenalty,
  geographicallyAllowed,
  itineraryRegionCount,
  maxMajorRegionsForDays,
  regionRelationship,
  startingRegion,
} from "../assets/js/app/ai/geographic-intelligence.js";


test("destinations map to geographic tourism regions", () => {
  assert.equal(
    destinationRegion({ slug: "tripoli" }),
    "northwest",
  );

  assert.equal(
    destinationRegion({ slug: "benghazi" }),
    "east",
  );

  assert.equal(
    destinationRegion({ slug: "ghadames" }),
    "westernDesert",
  );

  assert.equal(
    destinationRegion({ slug: "acacus" }),
    "southwest",
  );
});


test("starting points map to geographic regions", () => {
  assert.equal(
    startingRegion("tripoli"),
    "northwest",
  );

  assert.equal(
    startingRegion("benghazi"),
    "east",
  );

  assert.equal(
    startingRegion("sebha"),
    "southwest",
  );
});


test("three day trips are limited to one major region", () => {
  assert.equal(
    maxMajorRegionsForDays(3),
    1,
  );
});


test("four to six day trips allow two regions", () => {
  assert.equal(
    maxMajorRegionsForDays(5),
    2,
  );
});


test("week long trips allow broader movement", () => {
  assert.equal(
    maxMajorRegionsForDays(7),
    3,
  );
});


test("same region has no geographic penalty", () => {
  assert.equal(
    geographicPenalty({
      destination: { slug: "green-mountain" },
      startingPoint: "benghazi",
      days: 3,
    }),
    0,
  );
});


test("three day eastern trip strongly penalizes Ghadames", () => {
  assert.equal(
    geographicPenalty({
      destination: { slug: "ghadames" },
      startingPoint: "benghazi",
      days: 3,
    }),
    70,
  );
});


test("longer trips reduce distant-region penalty", () => {
  assert.ok(
    geographicPenalty({
      destination: { slug: "ghadames" },
      startingPoint: "benghazi",
      days: 8,
    }) <
    geographicPenalty({
      destination: { slug: "ghadames" },
      startingPoint: "benghazi",
      days: 3,
    }),
  );
});


test("east and eastern oases are adjacent", () => {
  assert.equal(
    regionRelationship(
      "east",
      "easternOases",
    ),
    "adjacent",
  );
});


test("east and western desert are distant", () => {
  assert.equal(
    regionRelationship(
      "east",
      "westernDesert",
    ),
    "distant",
  );
});


test("region count ignores repeated destinations in same region", () => {
  assert.equal(
    itineraryRegionCount([
      { slug: "benghazi" },
      { slug: "green-mountain" },
      { slug: "bomba-bay" },
    ]),
    1,
  );
});


test("three day itinerary rejects multiple major regions", () => {
  assert.equal(
    geographicallyAllowed(
      [
        { slug: "benghazi" },
        { slug: "ghadames" },
      ],
      3,
    ),
    false,
  );
});


test("week itinerary may span multiple regions", () => {
  assert.equal(
    geographicallyAllowed(
      [
        { slug: "benghazi" },
        { slug: "awjila" },
        { slug: "acacus" },
      ],
      7,
    ),
    true,
  );
});
