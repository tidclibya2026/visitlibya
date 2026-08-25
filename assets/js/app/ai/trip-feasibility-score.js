function numberOrZero(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : 0;
}


function collectDays(itinerary) {
  return Array.isArray(itinerary?.days)
    ? itinerary.days
    : [];
}


function collectDestinations(days) {
  return days.flatMap(
    (day) =>
      Array.isArray(day?.destinations)
        ? day.destinations
        : [],
  );
}


export function itineraryEvidence(
  itinerary,
) {
  const days =
    collectDays(itinerary);

  const destinations =
    collectDestinations(days);

  let unscheduledStops = 0;
  let highIntensityDays = 0;
  let moderateIntensityDays = 0;
  let longTravelDays = 0;
  let specialAccessStops = 0;
  let conflictAdjustedItems = 0;
  let totalTravelMinutes = 0;
  let totalVisitMinutes = 0;
  let totalRecoveryMinutes = 0;

  for (const day of days) {
    const summary =
      day?.summary ?? {};

    totalTravelMinutes +=
      numberOrZero(
        summary.travelMinutes,
      );

    totalVisitMinutes +=
      numberOrZero(
        summary.visitMinutes,
      );

    totalRecoveryMinutes +=
      numberOrZero(
        summary.recoveryMinutes,
      );

    if (
      summary.intensity === "high"
    ) {
      highIntensityDays += 1;
    }

    if (
      summary.intensity ===
      "moderate"
    ) {
      moderateIntensityDays += 1;
    }

    if (
      numberOrZero(
        summary.travelMinutes,
      ) >= 360
    ) {
      longTravelDays += 1;
    }

    const timeline =
      Array.isArray(day?.timeline)
        ? day.timeline
        : [];

    for (const item of timeline) {
      if (
        item?.type ===
          "destination" &&
        item?.scheduled === false
      ) {
        unscheduledStops += 1;
      }

      if (
        item?.conflictAdjusted
      ) {
        conflictAdjustedItems += 1;
      }
    }
  }

  for (const destination of destinations) {
    const score =
      destination?.planner_score ??
      {};

    if (
      score.requires4x4 ||
      score.requiresGuide
    ) {
      specialAccessStops += 1;
    }
  }

  return {
    dayCount: days.length,
    destinationCount:
      destinations.length,

    unscheduledStops,
    highIntensityDays,
    moderateIntensityDays,
    longTravelDays,
    specialAccessStops,
    conflictAdjustedItems,

    totalTravelMinutes,
    totalVisitMinutes,
    totalRecoveryMinutes,
  };
}


export function feasibilityPenalty(
  evidence,
) {
  let penalty = 0;

  penalty +=
    numberOrZero(
      evidence?.unscheduledStops,
    ) * 18;

  penalty +=
    numberOrZero(
      evidence?.highIntensityDays,
    ) * 8;

  penalty +=
    numberOrZero(
      evidence?.longTravelDays,
    ) * 7;

  penalty +=
    numberOrZero(
      evidence?.specialAccessStops,
    ) * 3;

  penalty +=
    Math.min(
      numberOrZero(
        evidence?.conflictAdjustedItems,
      ) * 2,
      8,
    );

  const travelMinutes =
    numberOrZero(
      evidence?.totalTravelMinutes,
    );

  const visitMinutes =
    numberOrZero(
      evidence?.totalVisitMinutes,
    );

  if (
    travelMinutes > 0 &&
    visitMinutes > 0 &&
    travelMinutes >
      visitMinutes * 0.9
  ) {
    penalty += 8;
  }

  const recoveryMinutes =
    numberOrZero(
      evidence?.totalRecoveryMinutes,
    );

  const dayCount =
    Math.max(
      1,
      numberOrZero(
        evidence?.dayCount,
      ),
    );

  if (
    recoveryMinutes /
      dayCount <
    30
  ) {
    penalty += 5;
  }

  return Math.min(
    100,
    Math.round(penalty),
  );
}


export function feasibilityRating(
  score,
) {
  const value =
    Number(score);

  if (!Number.isFinite(value)) {
    return "unknown";
  }

  if (value >= 90) {
    return "excellent";
  }

  if (value >= 75) {
    return "good";
  }

  if (value >= 60) {
    return "fair";
  }

  return "needs-review";
}


export function feasibilityMessages(
  evidence,
) {
  const warnings = [];
  const strengths = [];

  if (
    numberOrZero(
      evidence?.unscheduledStops,
    ) > 0
  ) {
    warnings.push(
      "unscheduled-stops",
    );
  } else {
    strengths.push(
      "all-stops-scheduled",
    );
  }

  if (
    numberOrZero(
      evidence?.highIntensityDays,
    ) > 0
  ) {
    warnings.push(
      "high-intensity-days",
    );
  } else {
    strengths.push(
      "balanced-daily-intensity",
    );
  }

  if (
    numberOrZero(
      evidence?.longTravelDays,
    ) > 0
  ) {
    warnings.push(
      "long-travel-days",
    );
  }

  if (
    numberOrZero(
      evidence?.specialAccessStops,
    ) > 0
  ) {
    warnings.push(
      "special-access-required",
    );
  }

  if (
    numberOrZero(
      evidence?.conflictAdjustedItems,
    ) === 0
  ) {
    strengths.push(
      "no-timeline-conflicts",
    );
  }

  if (
    numberOrZero(
      evidence?.totalRecoveryMinutes,
    ) > 0
  ) {
    strengths.push(
      "recovery-time-included",
    );
  }

  return {
    warnings,
    strengths,
  };
}


export function tripFeasibility(
  itinerary,
) {
  const evidence =
    itineraryEvidence(
      itinerary,
    );

  const penalty =
    feasibilityPenalty(
      evidence,
    );

  const score =
    Math.max(
      0,
      100 - penalty,
    );

  const messages =
    feasibilityMessages(
      evidence,
    );

  return {
    score,
    rating:
      feasibilityRating(
        score,
      ),

    penalty,

    warnings:
      messages.warnings,

    strengths:
      messages.strengths,

    evidence,
  };
}
