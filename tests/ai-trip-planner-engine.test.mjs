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


test("coordinate data overrides static regional route order", () => {
  const destinations = [
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      latitude: 32.1167,
      longitude: 20.0667,
    },
    {
      slug: "green-mountain",
      category_key: "mountains-nature",
      description_en: "Green Mountain",
      latitude: 32.3,
      longitude: 20.3,
    },
    {
      slug: "bomba-bay",
      category_key: "mediterranean-coast",
      description_en: "Bomba Bay",
      latitude: 32.2,
      longitude: 20.15,
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
      "bomba-bay",
      "green-mountain",
    ],
  );
});


test("planner exposes coordinate routing evidence when available", () => {
  const ranked = rankPlannerDestinations(
    [
      {
        slug: "benghazi",
        category_key: "historic-cities",
        description_en: "Benghazi",
        latitude: 32.1167,
        longitude: 20.0667,
      },
    ],
    {
      days: 3,
      startingPoint: "benghazi",
      interests: ["history"],
      travelerType: "solo",
      pace: "balanced",
    },
  );

  assert.equal(
    ranked[0].score.routingMode,
    "travel-time",
  );

  assert.equal(
    ranked[0].score.distanceKm,
    0,
  );
});


test("planner falls back to region routing without coordinates", () => {
  const ranked = rankPlannerDestinations(
    [
      {
        slug: "green-mountain",
        category_key: "mountains-nature",
        description_en: "Green Mountain",
      },
    ],
    {
      days: 3,
      startingPoint: "benghazi",
      interests: ["nature"],
      travelerType: "solo",
      pace: "balanced",
    },
  );

  assert.equal(
    ranked[0].score.routingMode,
    "region",
  );

  assert.equal(
    ranked[0].score.coordinatePenalty,
    null,
  );
});

test("planner exposes travel time routing evidence when coordinates exist", () => {
  const ranked =
    rankPlannerDestinations(
      [
        {
          slug: "benghazi",
          category_key: "historic-cities",
          description_en: "Benghazi",
          latitude: 32.1167,
          longitude: 20.0667,
        },
      ],
      {
        days: 3,
        startingPoint: "benghazi",
        interests: ["history"],
        travelerType: "solo",
        pace: "balanced",
      },
    );

  assert.equal(
    ranked[0].score.routingMode,
    "travel-time",
  );

  assert.equal(
    ranked[0].score.travelTimeMinutes,
    0,
  );

  assert.equal(
    ranked[0].score.exceedsDailyTravelBudget,
    false,
  );
});


test("planner falls back to regional routing without coordinate evidence", () => {
  const ranked =
    rankPlannerDestinations(
      [
        {
          slug: "green-mountain",
          category_key: "mountains-nature",
          description_en: "Green Mountain",
        },
      ],
      {
        days: 3,
        startingPoint: "benghazi",
        interests: ["nature"],
        travelerType: "solo",
        pace: "balanced",
      },
    );

  assert.equal(
    ranked[0].score.routingMode,
    "region",
  );

  assert.equal(
    ranked[0].score.travelTimeMinutes,
    null,
  );
});


test("relaxed itinerary reserves travel day when coordinate travel budget is exceeded", () => {
  const destinations = [
    {
      slug: "tripoli",
      category_key: "historic-cities",
      description_en: "Tripoli",
      latitude: 32.8872,
      longitude: 13.1913,
    },
    {
      slug: "sabratha",
      category_key: "archaeology",
      description_en: "Sabratha",
      latitude: 32.7933,
      longitude: 12.4885,
    },
    {
      slug: "benghazi",
      category_key: "historic-cities",
      description_en: "Benghazi",
      latitude: 32.1167,
      longitude: 20.0667,
    },
  ];

  const result =
    buildSuggestedItinerary(
      destinations,
      {
        days: 7,
        startingPoint: "tripoli",
        interests: [
          "history",
          "heritage",
        ],
        travelerType: "solo",
        pace: "relaxed",
      },
    );

  const travelDays =
    result.days.filter(
      (day) => day.type === "travel",
    );

  assert.ok(
    travelDays.length >= 1,
  );
});

test("Acacus exposes special road access requirements", () => {
  const ranked =
    rankPlannerDestinations(
      [
        {
          slug: "acacus",
          category_key: "desert",
          description_en: "Acacus",
          latitude: 24.8333,
          longitude: 10.3333,
        },
      ],
      {
        days: 7,
        startingPoint: "sebha",
        interests: ["desert"],
        travelerType: "solo",
        pace: "balanced",
      },
    );

  const score = ranked[0].score;

  assert.equal(
    score.requires4x4,
    true,
  );

  assert.equal(
    score.requiresGuide,
    true,
  );

  assert.equal(
    score.roadAccessClass,
    "desert-expedition",
  );
});


test("road adjustment increases remote travel estimate", () => {
  const ranked =
    rankPlannerDestinations(
      [
        {
          slug: "awjila",
          category_key: "oases",
          description_en: "Awjila",
          latitude: 29.1081,
          longitude: 21.2869,
        },
      ],
      {
        days: 7,
        startingPoint: "benghazi",
        interests: ["heritage"],
        travelerType: "solo",
        pace: "balanced",
      },
    );

  const score = ranked[0].score;

  assert.ok(
    score.adjustedRoadTravelMinutes >
    score.travelTimeMinutes,
  );
});


test("standard road keeps travel estimate unchanged", () => {
  const ranked =
    rankPlannerDestinations(
      [
        {
          slug: "tripoli",
          category_key: "historic-cities",
          description_en: "Tripoli",
          latitude: 32.8872,
          longitude: 13.1913,
        },
      ],
      {
        days: 3,
        startingPoint: "tripoli",
        interests: ["history"],
        travelerType: "solo",
        pace: "balanced",
      },
    );

  const score = ranked[0].score;

  assert.equal(
    score.adjustedRoadTravelMinutes,
    score.travelTimeMinutes,
  );
});
