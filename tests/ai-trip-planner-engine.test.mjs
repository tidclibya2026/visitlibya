import assert from "node:assert/strict";
import test from "node:test";

import {
  buildSuggestedItinerary,
  rankPlannerDestinations,
} from "../assets/js/app/ai/trip-planner-engine.js";

const destinations = [
  {
    slug: "tripoli",
    description_en: "Historic Mediterranean capital.",
    category_key: "historic-cities",
    region_en: "Tripoli · Mediterranean Coast",
    region_ar: "طرابلس · الساحل المتوسطي",
  },
  {
    slug: "sabratha",
    description_en: "UNESCO archaeological coastal city.",
    category_key: "archaeological-sites",
    region_en: "Sabratha · Northwest Coast",
    region_ar: "صبراتة · الساحل الشمالي الغربي",
  },
  {
    slug: "ghadames",
    description_en: "UNESCO oasis city.",
    category_key: "oases-heritage",
    region_en: "Ghadames · Western Desert",
    region_ar: "غدامس · الصحراء الغربية",
  },
  {
    slug: "green-mountain",
    description_en: "Forests and valleys.",
    category_key: "mountains-nature",
    region_en: "Cyrenaica · Northeast Libya",
    region_ar: "برقة · شمال شرق ليبيا",
  },
  {
    slug: "desert",
    description_en: "Dunes and desert landscapes.",
    category_key: "sahara-desert",
    region_en: "Sahara · Southern Libya",
    region_ar: "الصحراء الكبرى · جنوب ليبيا",
  },
];

test("historic northwest destinations rank highly", () => {
  const ranked = rankPlannerDestinations(destinations, {
    startingPoint: "tripoli",
    interests: ["history", "heritage"],
    travelerType: "family",
  });

  const firstTwo = ranked.slice(0, 2).map(
    (entry) => entry.destination.slug,
  );

  assert.ok(firstTwo.includes("tripoli"));
  assert.ok(firstTwo.includes("sabratha"));
});

test("desert preference prioritizes desert", () => {
  const ranked = rankPlannerDestinations(destinations, {
    startingPoint: "sebha",
    interests: ["desert"],
    travelerType: "group",
  });

  assert.equal(ranked[0].destination.slug, "desert");
});

test("balanced pace uses at most two stops per day", () => {
  const itinerary = buildSuggestedItinerary(destinations, {
    days: 3,
    interests: ["history", "heritage", "nature"],
    pace: "balanced",
  });

  assert.equal(itinerary.days.length, 3);

  for (const day of itinerary.days) {
    assert.ok(day.destinations.length <= 2);
  }
});

test("relaxed pace uses at most one stop per day", () => {
  const itinerary = buildSuggestedItinerary(destinations, {
    days: 3,
    interests: ["history", "heritage", "nature"],
    pace: "relaxed",
  });

  for (const day of itinerary.days) {
    assert.ok(day.destinations.length <= 1);
  }
});

test("active pace uses at most three stops per day", () => {
  const itinerary = buildSuggestedItinerary(destinations, {
    days: 2,
    interests: ["history", "heritage", "nature", "desert"],
    pace: "active",
  });

  for (const day of itinerary.days) {
    assert.ok(day.destinations.length <= 3);
  }
});

test("day count is clamped", () => {
  const low = buildSuggestedItinerary(destinations, {
    days: 0,
    interests: ["history"],
  });

  const high = buildSuggestedItinerary(destinations, {
    days: 50,
    interests: ["history"],
  });

  assert.equal(low.days.length, 1);
  assert.equal(high.days.length, 14);
});

test("invalid destinations are ignored", () => {
  const ranked = rankPlannerDestinations(
    [
      ...destinations,
      {},
      { slug: "broken" },
      { category_key: "historic-cities" },
    ],
    { interests: ["history"] },
  );

  assert.equal(ranked.length, destinations.length);
});

test("equal scores are deterministic", () => {
  const ranked = rankPlannerDestinations(
    [
      {
        slug: "beta",
        category_key: "historic-cities",
        description_en: "B",
      },
      {
        slug: "alpha",
        category_key: "historic-cities",
        description_en: "A",
      },
    ],
    { interests: ["history"] },
  );

  assert.deepEqual(
    ranked.map((entry) => entry.destination.slug),
    ["alpha", "beta"],
  );
});

test("score details are exposed", () => {
  const ranked = rankPlannerDestinations(destinations, {
    startingPoint: "tripoli",
    interests: ["history"],
    travelerType: "family",
  });

  assert.equal(typeof ranked[0].score.total, "number");
  assert.equal(typeof ranked[0].score.interestScore, "number");
  assert.equal(typeof ranked[0].score.startingRegionScore, "number");
  assert.equal(typeof ranked[0].score.travelerScore, "number");
  assert.equal(typeof ranked[0].score.contentScore, "number");
});
