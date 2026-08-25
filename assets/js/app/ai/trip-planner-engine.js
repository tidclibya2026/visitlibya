import {
  destinationRegion,
  geographicPenalty,
  maxMajorRegionsForDays,
  startingRegion,
} from "./geographic-intelligence.js";

import {
  orderDestinationsWithinRegion,
} from "./route-sequencing.js";

import {
  requiresTravelDay,
} from "./travel-day-planner.js";

import {
  coordinateTravelPenalty,
  orderByNearestCoordinate,
  startingPointCoordinates,
  validCoordinates,
} from "./coordinate-routing.js";

import {
  requiresTravelTimeDay,
  travelTimePenalty,
} from "./travel-time-intelligence.js";

import {
  adjustedRoadTravelMinutes,
  roadFeasibilityEvidence,
  roadFeasibilityPenalty,
} from "./road-feasibility.js";

import {
  canAddDestinationToDay,
  dailyVisitBudgetMinutes,
  visitBudgetStatus,
  visitDurationMinutes,
} from "./visit-duration-intelligence.js";

import {
  formatClockMinutes,
  scheduleDestinationSequence,
} from "./opening-hours-intelligence.js";

import {
  insertMealAndRestStops,
} from "./meal-rest-intelligence.js";

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

  const interestScore =
    scoreInterestMatch(destination, interests);

  const startingRegionScore =
    scoreStartingRegion(
      destination,
      preferences.startingPoint,
    );

  const travelerScore =
    scoreTravelerType(
      destination,
      preferences.travelerType,
    );

  const contentScore =
    destination.description_en ||
    destination.description_ar
      ? 5
      : 0;

  const regionalPenalty = geographicPenalty({
    destination,
    startingPoint: preferences.startingPoint,
    days: preferences.days,
  });

  const originCoordinates =
    startingPointCoordinates(
      preferences.startingPoint,
    );

  const coordinateResult =
    coordinateTravelPenalty({
      source: originCoordinates,
      target: destination,
      days: preferences.days,
      pace: preferences.pace,
    });

  const travelTimeResult =
    travelTimePenalty({
      source: originCoordinates,
      target: destination,
      days: preferences.days,
      pace: preferences.pace,
    });

  const roadEvidence =
    roadFeasibilityEvidence(
      destination,
    );

  const adjustedTravelMinutes =
    adjustedRoadTravelMinutes(
      travelTimeResult.minutes,
      destination,
    );

  const roadPenalty =
    roadFeasibilityPenalty(
      destination,
    );

  const hasTravelTimeEvidence =
    travelTimeResult.minutes !== null;

  const hasCoordinateEvidence =
    coordinateResult.distanceKm !== null;

  const travelPenalty =
    hasTravelTimeEvidence
      ? travelTimeResult.penalty + roadPenalty
      : hasCoordinateEvidence
        ? coordinateResult.penalty + roadPenalty
        : regionalPenalty + roadPenalty;

  const tourismScore =
    interestScore +
    startingRegionScore +
    travelerScore +
    contentScore;

  return {
    total: tourismScore - travelPenalty,
    tourismScore,
    interestScore,
    startingRegionScore,
    travelerScore,
    contentScore,

    geographicPenalty:
      regionalPenalty,

    coordinatePenalty:
      hasCoordinateEvidence
        ? coordinateResult.penalty
        : null,

    distanceKm:
      coordinateResult.distanceKm,

    distanceBand:
      coordinateResult.band,

    travelTimeMinutes:
      travelTimeResult.minutes,

    adjustedRoadTravelMinutes:
      adjustedTravelMinutes,

    travelTimeBand:
      travelTimeResult.band,

    travelTimePenalty:
      hasTravelTimeEvidence
        ? travelTimeResult.penalty
        : null,

    roadFeasibilityPenalty:
      roadPenalty,

    roadAccessClass:
      roadEvidence.accessClass,

    roadFactor:
      roadEvidence.roadFactor,

    requires4x4:
      roadEvidence.requires4x4,

    requiresGuide:
      roadEvidence.requiresGuide,

    exceedsDailyTravelBudget:
      hasTravelTimeEvidence
        ? travelTimeResult.exceedsDailyBudget
        : null,

    routingMode:
      hasTravelTimeEvidence
        ? "travel-time"
        : hasCoordinateEvidence
          ? "coordinates"
          : "region",

    geographicRegion:
      destinationRegion(destination),
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

function selectGeographicallyCoherentDestinations(
  ranked,
  preferences,
  maximumStops,
) {
  const days = safeDayCount(preferences.days);

  const maximumRegions =
    maxMajorRegionsForDays(days);

  const originRegion =
    startingRegion(preferences.startingPoint);

  const selectedRegions = new Set();

  if (originRegion !== "unknown") {
    selectedRegions.add(originRegion);
  }

  const selected = [];

  for (const entry of ranked) {
    if (selected.length >= maximumStops) {
      break;
    }

    if (entry.score.total <= 0) {
      continue;
    }

    const region =
      destinationRegion(entry.destination);

    if (
      region !== "unknown" &&
      !selectedRegions.has(region) &&
      selectedRegions.size >= maximumRegions
    ) {
      continue;
    }

    selected.push(entry);

    if (region !== "unknown") {
      selectedRegions.add(region);
    }
  }

  return selected;
}


function orderSelectedDestinationsByRoute(
  selected,
  preferences,
) {
  const originRegion =
    startingRegion(preferences.startingPoint);

  const grouped = new Map();

  for (const entry of selected) {
    const region =
      destinationRegion(entry.destination);

    if (!grouped.has(region)) {
      grouped.set(region, []);
    }

    grouped.get(region).push(entry);
  }

  const orderedRegions = [
    originRegion,
    ...[...grouped.keys()].filter(
      (region) => region !== originRegion,
    ),
  ];

  const ordered = [];

  let currentCoordinates =
    startingPointCoordinates(
      preferences.startingPoint,
    );

  for (const region of orderedRegions) {
    const entries = grouped.get(region);

    if (!entries?.length) {
      continue;
    }

    const destinations =
      entries.map(
        (entry) => entry.destination,
      );

    const hasCoordinateData =
      Boolean(currentCoordinates) &&
      destinations.some(
        (destination) =>
          validCoordinates(destination),
      );

    const orderedDestinations =
      hasCoordinateData
        ? orderByNearestCoordinate(
            destinations,
            currentCoordinates,
          )
        : orderDestinationsWithinRegion(
            destinations,
            region,
          );

    const entriesBySlug = new Map(
      entries.map((entry) => [
        String(entry.destination.slug)
          .trim()
          .toLowerCase(),
        entry,
      ]),
    );

    for (const destination of orderedDestinations) {
      const slug =
        String(destination.slug)
          .trim()
          .toLowerCase();

      const entry =
        entriesBySlug.get(slug);

      if (!entry) {
        continue;
      }

      ordered.push(entry);

      const coordinates =
        validCoordinates(destination);

      if (coordinates) {
        currentCoordinates =
          coordinates;
      }
    }
  }

  return ordered;
}


function shouldReserveTravelDay(
  previousDestination,
  nextDestination,
  preferences,
) {
  const travelTimeDecision =
    requiresTravelTimeDay({
      source: previousDestination,
      target: nextDestination,
      pace: preferences.pace,
    });

  if (travelTimeDecision !== null) {
    return travelTimeDecision;
  }

  return requiresTravelDay(
    previousDestination,
    nextDestination,
  );
}


function allocateTravelAwareDays(
  selected,
  days,
  dailyCapacity,
  preferences,
) {
  const itineraryDays = Array.from(
    { length: days },
    (_, index) => ({
      dayNumber: index + 1,
      type: "visit",
      destinations: [],
    }),
  );

  let dayIndex = 0;
  let stopsToday = 0;
  let previousDestination = null;

  for (const entry of selected) {
    const destination = entry.destination;

    if (
      previousDestination &&
      shouldReserveTravelDay(
        previousDestination,
        destination,
        preferences,
      )
    ) {
      if (stopsToday > 0) {
        dayIndex += 1;
        stopsToday = 0;
      }

      if (dayIndex >= days) {
        break;
      }

      itineraryDays[dayIndex] = {
        dayNumber: dayIndex + 1,
        type: "travel",
        fromRegion:
          destinationRegion(
            previousDestination,
          ),
        toRegion:
          destinationRegion(
            destination,
          ),
        destinations: [],
      };

      dayIndex += 1;
      stopsToday = 0;

      if (dayIndex >= days) {
        break;
      }
    }

    if (stopsToday >= dailyCapacity) {
      dayIndex += 1;
      stopsToday = 0;
    }

    if (dayIndex >= days) {
      break;
    }

    itineraryDays[dayIndex].destinations.push({
      ...destination,
      planner_score: entry.score,
    });

    previousDestination = destination;
    stopsToday += 1;
  }

  return itineraryDays;
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

  const selected =
    selectGeographicallyCoherentDestinations(
      ranked,
      preferences,
      maximumStops,
    );

  const routeOrderedSelected =
    orderSelectedDestinationsByRoute(
      selected,
      preferences,
    );

  const itineraryDays =
    allocateTravelAwareDays(
      routeOrderedSelected,
      days,
      dailyCapacity,
      preferences,
    );

  for (const day of itineraryDays) {
    if (day.type === "travel") {
      day.visitBudget = {
        usedMinutes: 0,
        budgetMinutes:
          dailyVisitBudgetMinutes(
            preferences.pace,
          ),
        remainingMinutes:
          dailyVisitBudgetMinutes(
            preferences.pace,
          ),
        exceedsBudget: false,
      };

      continue;
    }

    day.destinations =
      day.destinations.map(
        (destination) => ({
          ...destination,

          planner_score: {
            ...(destination.planner_score ?? {}),

            estimatedVisitMinutes:
              visitDurationMinutes(
                destination,
                preferences.pace,
              ),
          },
        }),
      );

    day.destinations =
      day.destinations.map(
        (destination) => ({
          ...destination,

          planner_score: {
            ...(destination.planner_score ?? {}),

            estimatedVisitMinutes:
              visitDurationMinutes(
                destination,
                preferences.pace,
              ),
          },
        }),
      );

    day.visitBudget =
      visitBudgetStatus({
        destinations:
          day.destinations,
        pace:
          preferences.pace,
      });

    const scheduledDestinations =
      scheduleDestinationSequence({
        destinations:
          day.destinations,
        pace:
          preferences.pace,

        visitDurationResolver:
          (destination) =>
            visitDurationMinutes(
              destination,
              preferences.pace,
            ),
      });

    day.destinations =
      scheduledDestinations.map(
        (scheduledItem) => ({
          ...scheduledItem.destination,

          planner_score: {
            ...(
              scheduledItem
                .destination
                .planner_score ?? {}
            ),

            scheduled:
              scheduledItem.scheduled,

            scheduledStartMinutes:
              scheduledItem.startsAt,

            scheduledEndMinutes:
              scheduledItem.endsAt,

            scheduledStart:
              scheduledItem.startsAt === null
                ? null
                : formatClockMinutes(
                    scheduledItem.startsAt,
                  ),

            scheduledEnd:
              scheduledItem.endsAt === null
                ? null
                : formatClockMinutes(
                    scheduledItem.endsAt,
                  ),

            openingHoursStatus:
              scheduledItem.openingStatus,

            scheduleReason:
              scheduledItem.reason,
          },
        }),
      );

    day.timeline =
      insertMealAndRestStops({
        scheduledItems:
          scheduledDestinations,
        pace:
          preferences.pace,
      }).map((item) => {
        if (
          item?.type === "meal" ||
          item?.type === "rest"
        ) {
          return {
            ...item,

            startsAtLabel:
              formatClockMinutes(
                item.startsAt,
              ),

            endsAtLabel:
              formatClockMinutes(
                item.endsAt,
              ),
          };
        }

        return {
          type: "destination",
          destination:
            item.destination,
          scheduled:
            item.scheduled,
          reason:
            item.reason,
          openingStatus:
            item.openingStatus,
          startsAt:
            item.startsAt,
          endsAt:
            item.endsAt,

          startsAtLabel:
            item.startsAt === null
              ? null
              : formatClockMinutes(
                  item.startsAt,
                ),

          endsAtLabel:
            item.endsAt === null
              ? null
              : formatClockMinutes(
                  item.endsAt,
                ),
        };
      });
  }

  const actualSelectedCount =
    itineraryDays.reduce(
      (total, day) =>
        total + day.destinations.length,
      0,
    );

  return {
    days: itineraryDays,
    selectedCount: actualSelectedCount,
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
