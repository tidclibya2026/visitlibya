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

test("three day Benghazi trip stays in eastern region", () => {
  const destinations = [
    {
      slug: "benghazi",
      category_key: "historic-cities",
      region_en: "Benghazi · Eastern Libya",
      description_en: "Benghazi",
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      region_en: "Cyrenaica · Northeast Libya",
      description_en: "Green Mountain",
    },
    {
      slug: "bomba-bay",
      category_key: "mediterranean-coast",
      region_en: "Derna District · Northeast Coast",
      description_en: "Bomba Bay",
    },
    {
      slug: "ghadames",
      category_key: "oases-heritage",
      region_en: "Ghadames · Western Desert",
      description_en: "Ghadames",
    },
    {
      slug: "acacus",
      category_key: "sahara-rock-art",
      region_en: "Fezzan · Southwest Libya",
      description_en: "Acacus",
    },
  ];

  const result = buildSuggestedItinerary(
    destinations,
    {
      days: 3,
      startingPoint: "benghazi",
      interests: [
        "history",
        "nature",
        "heritage",
        "desert",
      ],
      travelerType: "solo",
      pace: "balanced",
    },
  );

  const slugs = result.days.flatMap(
    (day) =>
      day.destinations.map(
        (destination) => destination.slug,
      ),
  );

  assert.ok(slugs.includes("benghazi"));
  assert.ok(slugs.includes("green-mountain"));

  assert.equal(
    slugs.includes("ghadames"),
    false,
  );

  assert.equal(
    slugs.includes("acacus"),
    false,
  );
});


test("short eastern trip applies strong penalty to Ghadames", () => {
  const ranked = rankPlannerDestinations(
    [
      {
        slug: "benghazi",
        category_key: "historic-cities",
        description_en: "Benghazi",
        region_en: "Eastern Libya",
      },
      {
        slug: "ghadames",
        category_key: "oases-heritage",
        description_en: "Ghadames",
        region_en: "Western Desert",
      },
    ],
    {
      days: 3,
      startingPoint: "benghazi",
      interests: [
        "history",
        "heritage",
      ],
      travelerType: "solo",
    },
  );

  const ghadames = ranked.find(
    (entry) =>
      entry.destination.slug === "ghadames",
  );

  assert.equal(
    ghadames.score.geographicPenalty,
    70,
  );

  assert.ok(
    ghadames.score.total <
    ghadames.score.tourismScore,
  );
});


test("week trip may include a second distant tourism region", () => {
  const destinations = [
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      region_en: "Eastern Libya",
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      description_en: "Green Mountain",
      region_en: "Cyrenaica",
    },
    {
      slug: "awjila",
      category_key: "oases-nature",
      description_en: "Awjila",
      region_en: "Eastern Libya",
    },
    {
      slug: "ghadames",
      category_key: "oases-heritage",
      description_en: "Ghadames",
      region_en: "Western Desert",
    },
  ];

  const result = buildSuggestedItinerary(
    destinations,
    {
      days: 7,
      startingPoint: "benghazi",
      interests: [
        "history",
        "heritage",
        "nature",
      ],
      travelerType: "solo",
      pace: "balanced",
    },
  );

  const slugs = result.days.flatMap(
    (day) =>
      day.destinations.map(
        (destination) => destination.slug,
      ),
  );

  assert.ok(
    slugs.includes("benghazi"),
  );

  assert.ok(
    slugs.includes("ghadames") ||
    slugs.includes("awjila"),
  );
});

test("eastern itinerary follows route sequence", () => {
  const destinations = [
    {
      slug: "bomba-bay",
      category_key: "mediterranean-coast",
      description_en: "Bomba Bay",
      region_en: "Northeast Coast",
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      description_en: "Green Mountain",
      region_en: "Cyrenaica",
    },
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      region_en: "Eastern Libya",
    },
  ];

  const result = buildSuggestedItinerary(
    destinations,
    {
      days: 3,
      startingPoint: "benghazi",
      interests: [
        "history",
        "nature",
        "coast",
      ],
      travelerType: "solo",
      pace: "relaxed",
    },
  );

  const slugs = result.days.flatMap(
    (day) =>
      day.destinations.map(
        (destination) => destination.slug,
      ),
  );

  assert.deepEqual(
    slugs,
    [
      "benghazi",
      "green-mountain",
      "bomba-bay",
    ],
  );
});

test("distant region transition consumes a dedicated travel day", () => {
  const destinations = [
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      region_en: "Eastern Libya",
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      description_en: "Green Mountain",
      region_en: "Cyrenaica",
    },
    {
      slug: "ghadames",
      category_key: "oases-heritage",
      description_en: "Ghadames",
      region_en: "Western Desert",
    },
  ];

  const result = buildSuggestedItinerary(
    destinations,
    {
      days: 7,
      startingPoint: "benghazi",
      interests: [
        "history",
        "heritage",
        "nature",
      ],
      travelerType: "solo",
      pace: "relaxed",
    },
  );

  const travelDayIndex =
    result.days.findIndex(
      (day) => day.type === "travel",
    );

  assert.ok(travelDayIndex >= 0);

  assert.equal(
    result.days[travelDayIndex]
      .destinations.length,
    0,
  );

  const ghadamesDayIndex =
    result.days.findIndex(
      (day) =>
        day.destinations.some(
          (destination) =>
            destination.slug === "ghadames",
        ),
    );

  assert.ok(
    ghadamesDayIndex > travelDayIndex,
  );
});


test("three day eastern itinerary has no unnecessary travel day", () => {
  const destinations = [
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      region_en: "Eastern Libya",
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      description_en: "Green Mountain",
      region_en: "Cyrenaica",
    },
    {
      slug: "bomba-bay",
      category_key: "mediterranean-coast",
      description_en: "Bomba Bay",
      region_en: "Northeast Coast",
    },
  ];

  const result = buildSuggestedItinerary(
    destinations,
    {
      days: 3,
      startingPoint: "benghazi",
      interests: [
        "history",
        "nature",
        "coast",
      ],
      travelerType: "solo",
      pace: "relaxed",
    },
  );

  assert.equal(
    result.days.some(
      (day) => day.type === "travel",
    ),
    false,
  );
});

