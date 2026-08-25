import assert from "node:assert/strict";
import test from "node:test";

import {
  enrichPlannerDestinationsWithCoordinates,
} from "../assets/js/app/ai/coordinate-enrichment.js";


test("planner destinations receive catalogue coordinates", async () => {
  const result =
    await enrichPlannerDestinationsWithCoordinates(
      [
        {
          slug: "tripoli",
          name_en: "Tripoli",
        },
        {
          slug: "benghazi",
          name_en: "Benghazi",
        },
      ],
      {
        listDestinationCatalogue:
          async () => ({
            items: [
              {
                slug: "tripoli",
                latitude: 32.8872,
                longitude: 13.1913,
              },
              {
                slug: "benghazi",
                latitude: 32.1167,
                longitude: 20.0667,
              },
            ],
            pages: 1,
          }),
      },
    );

  assert.equal(
    result[0].latitude,
    32.8872,
  );

  assert.equal(
    result[0].longitude,
    13.1913,
  );

  assert.equal(
    result[1].latitude,
    32.1167,
  );
});


test("missing catalogue coordinates preserve destination", async () => {
  const result =
    await enrichPlannerDestinationsWithCoordinates(
      [
        {
          slug: "tripoli",
          latitude: 32.8,
          longitude: 13.1,
        },
      ],
      {
        listDestinationCatalogue:
          async () => ({
            items: [
              {
                slug: "tripoli",
                latitude: null,
                longitude: null,
              },
            ],
            pages: 1,
          }),
      },
    );

  assert.equal(
    result[0].latitude,
    32.8,
  );

  assert.equal(
    result[0].longitude,
    13.1,
  );
});


test("destination without catalogue match remains available", async () => {
  const source = {
    slug: "unknown-place",
    name_en: "Unknown Place",
  };

  const result =
    await enrichPlannerDestinationsWithCoordinates(
      [source],
      {
        listDestinationCatalogue:
          async () => ({
            items: [],
            pages: 1,
          }),
      },
    );

  assert.equal(
    result[0].slug,
    "unknown-place",
  );
});


test("invalid catalogue response is rejected", async () => {
  await assert.rejects(
    () =>
      enrichPlannerDestinationsWithCoordinates(
        [
          {
            slug: "tripoli",
          },
        ],
        {
          listDestinationCatalogue:
            async () => ({
              invalid: true,
            }),
        },
      ),
    TypeError,
  );
});
