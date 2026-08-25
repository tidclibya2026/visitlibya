function numberOrZero(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : 0;
}


function normalizeDays(itinerary) {
  return Array.isArray(itinerary?.days)
    ? itinerary.days
    : [];
}


function collectSpecialAccessStops(days) {
  const result = [];

  for (const day of days) {
    const destinations =
      Array.isArray(day?.destinations)
        ? day.destinations
        : [];

    for (const destination of destinations) {
      const score =
        destination?.planner_score ?? {};

      if (
        score.requires4x4 ||
        score.requiresGuide
      ) {
        result.push({
          dayNumber:
            day.dayNumber ?? null,

          slug:
            destination?.slug ?? null,

          requires4x4:
            Boolean(
              score.requires4x4,
            ),

          requiresGuide:
            Boolean(
              score.requiresGuide,
            ),
        });
      }
    }
  }

  return result;
}


function collectUnscheduledStops(days) {
  const result = [];

  for (const day of days) {
    const timeline =
      Array.isArray(day?.timeline)
        ? day.timeline
        : [];

    for (const item of timeline) {
      if (
        item?.type !== "destination" ||
        item?.scheduled !== false
      ) {
        continue;
      }

      result.push({
        dayNumber:
          day.dayNumber ?? null,

        slug:
          item.destination?.slug ??
          null,

        reason:
          item.reason ?? null,
      });
    }
  }

  return result;
}


function collectHighIntensityDays(days) {
  return days
    .filter(
      (day) =>
        day?.summary?.intensity ===
        "high",
    )
    .map(
      (day) => ({
        dayNumber:
          day.dayNumber ?? null,

        activityMinutes:
          numberOrZero(
            day?.summary
              ?.activityMinutes,
          ),

        recoveryMinutes:
          numberOrZero(
            day?.summary
              ?.recoveryMinutes,
          ),
      }),
    );
}


function collectLongTravelDays(days) {
  return days
    .filter(
      (day) =>
        numberOrZero(
          day?.summary
            ?.travelMinutes,
        ) >= 360,
    )
    .map(
      (day) => ({
        dayNumber:
          day.dayNumber ?? null,

        travelMinutes:
          numberOrZero(
            day?.summary
              ?.travelMinutes,
          ),
      }),
    );
}


function averageRecoveryMinutes(days) {
  if (!days.length) {
    return 0;
  }

  const total =
    days.reduce(
      (sum, day) =>
        sum +
        numberOrZero(
          day?.summary
            ?.recoveryMinutes,
        ),
      0,
    );

  return total / days.length;
}


function recommendation(
  code,
  priority,
  evidence = {},
) {
  return {
    code,
    priority,
    evidence,
  };
}


export function tripRecommendationEvidence(
  itinerary,
) {
  const days =
    normalizeDays(itinerary);

  const feasibility =
    itinerary?.feasibility ?? {};

  const highIntensityDays =
    collectHighIntensityDays(
      days,
    );

  const longTravelDays =
    collectLongTravelDays(
      days,
    );

  const unscheduledStops =
    collectUnscheduledStops(
      days,
    );

  const specialAccessStops =
    collectSpecialAccessStops(
      days,
    );

  return {
    feasibilityScore:
      numberOrZero(
        feasibility.score,
      ),

    feasibilityRating:
      feasibility.rating ??
      "unknown",

    highIntensityDays,
    longTravelDays,
    unscheduledStops,
    specialAccessStops,

    averageRecoveryMinutes:
      averageRecoveryMinutes(
        days,
      ),
  };
}


export function buildTripRecommendations(
  itinerary,
) {
  const evidence =
    tripRecommendationEvidence(
      itinerary,
    );

  const recommendations = [];

  if (
    evidence.unscheduledStops.length
  ) {
    recommendations.push(
      recommendation(
        "review-unscheduled-stops",
        "high",
        {
          stops:
            evidence.unscheduledStops,
        },
      ),
    );
  }

  if (
    evidence.longTravelDays.length
  ) {
    recommendations.push(
      recommendation(
        "separate-long-travel",
        "high",
        {
          days:
            evidence.longTravelDays,
        },
      ),
    );
  }

  if (
    evidence.highIntensityDays.length
  ) {
    recommendations.push(
      recommendation(
        "reduce-day-intensity",
        "medium",
        {
          days:
            evidence.highIntensityDays,
        },
      ),
    );
  }

  if (
    evidence.averageRecoveryMinutes <
    30
  ) {
    recommendations.push(
      recommendation(
        "increase-recovery-time",
        "medium",
        {
          averageRecoveryMinutes:
            Math.round(
              evidence
                .averageRecoveryMinutes,
            ),
        },
      ),
    );
  }

  if (
    evidence.specialAccessStops.length
  ) {
    recommendations.push(
      recommendation(
        "prepare-special-access",
        "medium",
        {
          stops:
            evidence.specialAccessStops,
        },
      ),
    );
  }

  if (
    evidence.feasibilityScore >= 90 &&
    !recommendations.some(
      (item) =>
        item.priority === "high",
    )
  ) {
    recommendations.push(
      recommendation(
        "itinerary-well-balanced",
        "info",
        {
          score:
            evidence.feasibilityScore,
        },
      ),
    );
  }

  return {
    evidence,
    recommendations,
  };
}


export function recommendationPriorityRank(
  priority,
) {
  switch (priority) {
    case "high":
      return 1;

    case "medium":
      return 2;

    case "low":
      return 3;

    case "info":
      return 4;

    default:
      return 99;
  }
}


export function sortTripRecommendations(
  recommendations,
) {
  if (!Array.isArray(recommendations)) {
    return [];
  }

  return [...recommendations]
    .sort(
      (left, right) =>
        recommendationPriorityRank(
          left?.priority,
        ) -
        recommendationPriorityRank(
          right?.priority,
        ),
    );
}
