const INTEREST_CATEGORY_WEIGHTS = {
  history: new Set([
    "historic-cities",
    "archaeological-sites",
    "oases-heritage",
    "mountains-heritage",
  ]),
  heritage: new Set([
    "historic-cities",
    "archaeological-sites",
    "oases-heritage",
    "mountains-heritage",
    "sahara-rock-art",
  ]),
  archaeology: new Set([
    "archaeological-sites",
    "sahara-rock-art",
  ]),
  desert: new Set([
    "sahara-desert",
    "sahara-rock-art",
    "oases-heritage",
    "oases-nature",
  ]),
  nature: new Set([
    "mountains-nature",
    "mediterranean-coast",
    "oases-nature",
    "sahara-desert",
  ]),
  coast: new Set([
    "mediterranean-coast",
  ]),
  culture: new Set([
    "historic-cities",
    "oases-heritage",
    "mountains-heritage",
  ]),
};

const START_REGION_KEYWORDS = {
  tripoli: [
    "tripoli",
    "northwest",
    "western",
    "طرابلس",
    "شمال غرب",
    "الغربية",
  ],
  benghazi: [
    "benghazi",
    "eastern",
    "northeast",
    "cyrenaica",
    "بنغازي",
    "شرق",
    "برقة",
  ],
  sebha: [
    "fezzan",
    "southern",
    "southwest",
    "sahara",
    "فزان",
    "جنوب",
    "الصحراء",
  ],
};

const TRAVELER_CATEGORY_BONUS = {
  family: new Set([
    "historic-cities",
    "archaeological-sites",
    "mountains-nature",
    "mediterranean-coast",
    "oases-nature",
  ]),
  couple: new Set([
    "historic-cities",
    "mountains-nature",
    "mediterranean-coast",
    "oases-heritage",
  ]),
  solo: new Set([
    "historic-cities",
    "archaeological-sites",
    "mountains-heritage",
    "sahara-rock-art",
    "sahara-desert",
  ]),
  group: new Set([
    "archaeological-sites",
    "sahara-rock-art",
    "sahara-desert",
    "mountains-nature",
  ]),
};

const PACE_STOPS_PER_DAY = {
  relaxed: 1,
  balanced: 2,
  active: 3,
};

function normalizeValue(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}

function normalizeList(values) {
  if (!Array.isArray(values)) {
    return [];
  }

  return values
    .map(normalizeValue)
    .filter(Boolean);
}

function destinationSearchText(destination) {
  return [
    destination.slug,
    destination.name_en,
    destination.name_ar,
    destination.description_en,
    destination.description_ar,
    destination.region_en,
    destination.region_ar,
    destination.category_en,
    destination.category_ar,
    destination.category_key,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function scoreInterestMatch(destination, interests) {
  if (!interests.length) {
    return 0;
  }

  const categoryKey = normalizeValue(destination.category_key);
  let matches = 0;

  for (const interest of interests) {
    const categories = INTEREST_CATEGORY_WEIGHTS[interest];

    if (categories?.has(categoryKey)) {
      matches += 1;
    }
  }

  if (!matches) {
    return 0;
  }

  return Math.min(
    40,
    Math.round((matches / interests.length) * 40),
  );
}

function scoreStartingRegion(destination, startingPoint) {
  const normalizedStart = normalizeValue(startingPoint);
  const keywords = START_REGION_KEYWORDS[normalizedStart];

  if (!keywords?.length) {
    return 0;
  }

  const searchable = destinationSearchText(destination);

  return keywords.some((keyword) =>
    searchable.includes(normalizeValue(keyword))
  )
    ? 25
    : 0;
}

function scoreTravelerType(destination, travelerType) {
  const categories =
    TRAVELER_CATEGORY_BONUS[normalizeValue(travelerType)];

  if (!categories) {
    return 0;
  }

  return categories.has(normalizeValue(destination.category_key))
    ? 10
    : 0;
}

function scoreDestination(destination, preferences) {
  const interests = normalizeList(preferences.interests);

  const interestScore = scoreInterestMatch(
    destination,
    interests,
  );

  const startingRegionScore = scoreStartingRegion(
    destination,
    preferences.startingPoint,
  );

  const travelerScore = scoreTravelerType(
    destination,
    preferences.travelerType,
  );

  const contentScore =
    destination.description_en || destination.description_ar
      ? 5
      : 0;

  return {
    total:
      interestScore +
      startingRegionScore +
      travelerScore +
      contentScore,
    interestScore,
    startingRegionScore,
    travelerScore,
    contentScore,
  };
}

export function rankPlannerDestinations(
  destinations,
  preferences = {},
) {
  if (!Array.isArray(destinations)) {
    return [];
  }

  return destinations
    .filter((destination) =>
      Boolean(
        destination?.slug &&
        destination?.category_key,
      ),
    )
    .map((destination) => ({
      destination,
      score: scoreDestination(
        destination,
        preferences,
      ),
    }))
    .sort((left, right) => {
      if (right.score.total !== left.score.total) {
        return right.score.total - left.score.total;
      }

      return String(left.destination.slug)
        .localeCompare(String(right.destination.slug));
    });
}

function stopsPerDay(pace) {
  return (
    PACE_STOPS_PER_DAY[normalizeValue(pace)] ??
    PACE_STOPS_PER_DAY.balanced
  );
}

function safeDayCount(days) {
  const parsed = Number(days);

  if (!Number.isInteger(parsed)) {
    return 3;
  }

  return Math.min(
    14,
    Math.max(1, parsed),
  );
}

export function buildSuggestedItinerary(
  destinations,
  preferences = {},
) {
  const days = safeDayCount(preferences.days);
  const dailyCapacity = stopsPerDay(preferences.pace);

  const ranked = rankPlannerDestinations(
    destinations,
    preferences,
  );

  const maximumStops = days * dailyCapacity;

  const selected = ranked
    .filter((entry) => entry.score.total > 0)
    .slice(0, maximumStops);

  const itineraryDays = Array.from(
    { length: days },
    (_, index) => ({
      dayNumber: index + 1,
      destinations: [],
    }),
  );

  selected.forEach((entry, index) => {
    const dayIndex = Math.floor(
      index / dailyCapacity,
    );

    if (itineraryDays[dayIndex]) {
      itineraryDays[dayIndex].destinations.push({
        ...entry.destination,
        planner_score: entry.score,
      });
    }
  });

  return {
    days: itineraryDays,
    selectedCount: selected.length,
    requestedDays: days,
    pace: normalizeValue(preferences.pace) || "balanced",
    preferences: {
      startingPoint:
        normalizeValue(preferences.startingPoint),
      interests:
        normalizeList(preferences.interests),
      travelerType:
        normalizeValue(preferences.travelerType),
    },
  };
}
