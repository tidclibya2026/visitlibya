import assert from "node:assert/strict";
import test from "node:test";

import {
  createTripFromSuggestedItinerary,
  flattenSuggestedItinerary,
  resolveSuggestedDestinationIds,
} from "../assets/js/app/ai/trip-planner-trip-creator.js";


const itinerary = {
  days: [
    {
      dayNumber: 1,
      destinations: [
        { slug: "tripoli" },
        { slug: "sabratha" },
      ],
    },
    {
      dayNumber: 2,
      destinations: [
        { slug: "ghadames" },
      ],
    },
  ],
};


test("flattenSuggestedItinerary preserves day order", () => {
  assert.deepEqual(
    flattenSuggestedItinerary(itinerary).map(
      (entry) => [
        entry.dayNumber,
        entry.destination.slug,
      ],
    ),
    [
      [1, "tripoli"],
      [1, "sabratha"],
      [2, "ghadames"],
    ],
  );
});


test("API disabled prevents creation", async () => {
  await assert.rejects(
    () =>
      createTripFromSuggestedItinerary({
        itinerary,
        apiEnabled: false,
        authenticatedUser: { id: 1 },
      }),
    (error) => error.code === "API_UNAVAILABLE",
  );
});


test("authentication is required", async () => {
  await assert.rejects(
    () =>
      createTripFromSuggestedItinerary({
        itinerary,
        apiEnabled: true,
        authenticatedUser: null,
      }),
    (error) => error.code === "AUTH_REQUIRED",
  );
});


test("empty itinerary cannot create a trip", async () => {
  await assert.rejects(
    () =>
      createTripFromSuggestedItinerary({
        itinerary: { days: [] },
        apiEnabled: true,
        authenticatedUser: { id: 1 },
      }),
    (error) => error.code === "EMPTY_ITINERARY",
  );
});


test("catalogue resolver maps slugs to authoritative ids", async () => {
  const result =
    await resolveSuggestedDestinationIds(
      [
        { slug: "tripoli" },
        { slug: "ghadames" },
      ],
      {
        listDestinationCatalogue: async () => ({
          items: [
            {
              id: 11,
              slug: "tripoli",
            },
            {
              id: 44,
              slug: "ghadames",
            },
          ],
          pages: 1,
        }),
      },
    );

  assert.equal(
    result.get("tripoli").id,
    11,
  );

  assert.equal(
    result.get("ghadames").id,
    44,
  );
});


test("missing destination fails before trip creation", async () => {
  let tripCreated = false;

  await assert.rejects(
    () =>
      createTripFromSuggestedItinerary({
        itinerary,
        locale: "en",
        apiEnabled: true,
        authenticatedUser: { id: 1 },

        listDestinationCatalogue:
          async () => ({
            items: [
              {
                id: 11,
                slug: "tripoli",
              },
            ],
            pages: 1,
          }),

        createTrip: async () => {
          tripCreated = true;
          return { id: 77 };
        },

        addTripItem: async () => ({}),
      }),
    (error) =>
      error.code === "DESTINATION_UNAVAILABLE",
  );

  assert.equal(
    tripCreated,
    false,
  );
});


test("planner creates a private draft trip", async () => {
  let payload = null;

  await createTripFromSuggestedItinerary({
    itinerary,
    locale: "en",
    apiEnabled: true,
    authenticatedUser: { id: 1 },

    listDestinationCatalogue:
      async () => ({
        items: [
          { id: 11, slug: "tripoli" },
          { id: 12, slug: "sabratha" },
          { id: 13, slug: "ghadames" },
        ],
        pages: 1,
      }),

    createTrip: async (value) => {
      payload = value;
      return { id: 77 };
    },

    addTripItem: async () => ({}),
  });

  assert.equal(payload.status, "draft");
  assert.equal(payload.visibility, "private");
  assert.equal(
    payload.title,
    "My Visit Libya Suggested Trip",
  );
});


test("Arabic planner creates localized metadata", async () => {
  let payload = null;

  await createTripFromSuggestedItinerary({
    itinerary,
    locale: "ar",
    apiEnabled: true,
    authenticatedUser: { id: 1 },

    listDestinationCatalogue:
      async () => ({
        items: [
          { id: 11, slug: "tripoli" },
          { id: 12, slug: "sabratha" },
          { id: 13, slug: "ghadames" },
        ],
        pages: 1,
      }),

    createTrip: async (value) => {
      payload = value;
      return { id: 77 };
    },

    addTripItem: async () => ({}),
  });

  assert.match(
    payload.title,
    /رحلتي/,
  );

  assert.equal(
    payload.visibility,
    "private",
  );
});


test("trip items preserve itinerary day and sort order", async () => {
  const createdItems = [];

  const trip =
    await createTripFromSuggestedItinerary({
      itinerary,
      locale: "en",
      apiEnabled: true,
      authenticatedUser: { id: 1 },

      listDestinationCatalogue:
        async () => ({
          items: [
            { id: 101, slug: "tripoli" },
            { id: 102, slug: "sabratha" },
            { id: 103, slug: "ghadames" },
          ],
          pages: 1,
        }),

      createTrip:
        async () => ({
          id: 900,
        }),

      addTripItem:
        async (tripId, payload) => {
          createdItems.push({
            tripId,
            ...payload,
          });

          return {
            id: createdItems.length,
          };
        },
    });

  assert.equal(trip.id, 900);

  assert.deepEqual(
    createdItems,
    [
      {
        tripId: 900,
        destination_id: 101,
        day_number: 1,
        sort_order: 1,
        notes: null,
      },
      {
        tripId: 900,
        destination_id: 102,
        day_number: 1,
        sort_order: 2,
        notes: null,
      },
      {
        tripId: 900,
        destination_id: 103,
        day_number: 2,
        sort_order: 3,
        notes: null,
      },
    ],
  );
});
