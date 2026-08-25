import assert from "node:assert/strict";
import test from "node:test";

import {
  coordinateTravelPenalty,
  distanceBand,
  distanceKm,
  orderByNearestCoordinate,
  requiresCoordinateTravelDay,
  validCoordinates,
} from "../assets/js/app/ai/coordinate-routing.js";


test("validCoordinates accepts valid latitude and longitude", () => {
  assert.deepEqual(
    validCoordinates({
      latitude: 32.8872,
      longitude: 13.1913,
    }),
    {
      latitude: 32.8872,
      longitude: 13.1913,
    },
  );
});


test("invalid coordinates are rejected", () => {
  assert.equal(
    validCoordinates({
      latitude: 120,
      longitude: 13,
    }),
    null,
  );
});


test("distanceKm returns zero for identical coordinates", () => {
  const point = {
    latitude: 32.8872,
    longitude: 13.1913,
  };

  assert.equal(
    distanceKm(point, point),
    0,
  );
});


test("distanceKm calculates realistic geodesic distance", () => {
  const distance =
    distanceKm(
      {
        latitude: 32.8872,
        longitude: 13.1913,
      },
      {
        latitude: 32.1167,
        longitude: 20.0667,
      },
    );

  assert.ok(distance > 600);
  assert.ok(distance < 700);
});


test("distance bands classify local travel", () => {
  assert.equal(
    distanceBand(40),
    "local",
  );

  assert.equal(
    distanceBand(150),
    "regional",
  );

  assert.equal(
    distanceBand(400),
    "long",
  );

  assert.equal(
    distanceBand(900),
    "very-long",
  );
});


test("short trip heavily penalizes very long transfer", () => {
  const result =
    coordinateTravelPenalty({
      source: {
        latitude: 32.8872,
        longitude: 13.1913,
      },
      target: {
        latitude: 32.1167,
        longitude: 20.0667,
      },
      days: 3,
      pace: "balanced",
    });

  assert.equal(
    result.band,
    "very-long",
  );

  assert.equal(
    result.penalty,
    100,
  );
});


test("long trip reduces very long distance penalty", () => {
  const shortTrip =
    coordinateTravelPenalty({
      source: {
        latitude: 32.8872,
        longitude: 13.1913,
      },
      target: {
        latitude: 32.1167,
        longitude: 20.0667,
      },
      days: 3,
    });

  const longTrip =
    coordinateTravelPenalty({
      source: {
        latitude: 32.8872,
        longitude: 13.1913,
      },
      target: {
        latitude: 32.1167,
        longitude: 20.0667,
      },
      days: 8,
    });

  assert.ok(
    longTrip.penalty <
    shortTrip.penalty,
  );
});


test("very long coordinate transfer requires travel day", () => {
  assert.equal(
    requiresCoordinateTravelDay(
      {
        latitude: 32.8872,
        longitude: 13.1913,
      },
      {
        latitude: 32.1167,
        longitude: 20.0667,
      },
    ),
    true,
  );
});


test("nearest-neighbor ordering follows coordinates", () => {
  const ordered =
    orderByNearestCoordinate(
      [
        {
          slug: "far",
          latitude: 33.0,
          longitude: 16.0,
        },
        {
          slug: "near",
          latitude: 32.9,
          longitude: 13.3,
        },
        {
          slug: "middle",
          latitude: 32.8,
          longitude: 14.2,
        },
      ],
      {
        latitude: 32.8872,
        longitude: 13.1913,
      },
    );

  assert.deepEqual(
    ordered.map((item) => item.slug),
    [
      "near",
      "middle",
      "far",
    ],
  );
});

test("starting point coordinates resolve Benghazi", async () => {
  const {
    startingPointCoordinates,
  } = await import(
    "../assets/js/app/ai/coordinate-routing.js"
  );

  assert.deepEqual(
    startingPointCoordinates("benghazi"),
    {
      latitude: 32.1167,
      longitude: 20.0667,
    },
  );
});


test("unknown starting point has no coordinates", async () => {
  const {
    startingPointCoordinates,
  } = await import(
    "../assets/js/app/ai/coordinate-routing.js"
  );

  assert.equal(
    startingPointCoordinates("unknown"),
    null,
  );
});
