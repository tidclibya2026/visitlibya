function cloneValue(value) {
  return JSON.parse(
    JSON.stringify(value),
  );
}


function normalizeDays(itinerary) {
  return Array.isArray(itinerary?.days)
    ? itinerary.days
    : [];
}


function destinationScore(destination) {
  const score =
    Number(
      destination
        ?.planner_score
        ?.total,
    );

  return Number.isFinite(score)
    ? score
    : 0;
}


function scheduledDestinationCount(day) {
  const timeline =
    Array.isArray(day?.timeline)
      ? day.timeline
      : [];

  return timeline.filter(
    (item) =>
      item?.type === "destination" &&
      item?.scheduled !== false,
  ).length;
}


function unscheduledDestinationSlugs(day) {
  const timeline =
    Array.isArray(day?.timeline)
      ? day.timeline
      : [];

  return new Set(
    timeline
      .filter(
        (item) =>
          item?.type ===
            "destination" &&
          item?.scheduled === false,
      )
      .map(
        (item) =>
          String(
            item?.destination?.slug ??
            "",
          )
            .trim()
            .toLowerCase(),
      )
      .filter(Boolean),
  );
}


export function optimizationEvidence(
  itinerary,
) {
  const days =
    normalizeDays(itinerary);

  const overloadedDays = [];
  const unscheduledStops = [];
  const longTravelDays = [];

  for (const day of days) {
    if (
      day?.summary?.intensity ===
      "high"
    ) {
      overloadedDays.push(
        day.dayNumber ?? null,
      );
    }

    const unscheduled =
      unscheduledDestinationSlugs(
        day,
      );

    for (const slug of unscheduled) {
      unscheduledStops.push({
        dayNumber:
          day.dayNumber ?? null,
        slug,
      });
    }

    const travelMinutes =
      Number(
        day?.summary
          ?.travelMinutes,
      );

    if (
      Number.isFinite(
        travelMinutes,
      ) &&
      travelMinutes >= 360
    ) {
      longTravelDays.push({
        dayNumber:
          day.dayNumber ?? null,
        travelMinutes,
      });
    }
  }

  return {
    overloadedDays,
    unscheduledStops,
    longTravelDays,
  };
}


export function removeUnscheduledStops(
  days,
) {
  if (!Array.isArray(days)) {
    return [];
  }

  return days.map((day) => {
    const copy =
      cloneValue(day);

    const unscheduled =
      unscheduledDestinationSlugs(
        day,
      );

    if (!unscheduled.size) {
      return copy;
    }

    copy.destinations =
      (
        Array.isArray(
          copy.destinations,
        )
          ? copy.destinations
          : []
      ).filter(
        (destination) =>
          !unscheduled.has(
            String(
              destination?.slug ??
              "",
            )
              .trim()
              .toLowerCase(),
          ),
      );

    return copy;
  });
}


export function reduceHighIntensityDays(
  days,
) {
  if (!Array.isArray(days)) {
    return [];
  }

  return days.map((day) => {
    const copy =
      cloneValue(day);

    if (
      day?.summary?.intensity !==
      "high"
    ) {
      return copy;
    }

    const destinations =
      Array.isArray(
        copy.destinations,
      )
        ? copy.destinations
        : [];

    if (
      destinations.length <= 1
    ) {
      return copy;
    }

    const sorted =
      [...destinations]
        .sort(
          (left, right) =>
            destinationScore(left) -
            destinationScore(right),
        );

    const removeSlug =
      String(
        sorted[0]?.slug ?? "",
      )
        .trim()
        .toLowerCase();

    copy.destinations =
      destinations.filter(
        (destination) =>
          String(
            destination?.slug ??
            "",
          )
            .trim()
            .toLowerCase() !==
          removeSlug,
      );

    return copy;
  });
}


export function optimizeItineraryStructure(
  itinerary,
) {
  const originalDays =
    normalizeDays(itinerary);

  const evidence =
    optimizationEvidence(
      itinerary,
    );

  let optimizedDays =
    removeUnscheduledStops(
      originalDays,
    );

  optimizedDays =
    reduceHighIntensityDays(
      optimizedDays,
    );

  return {
    originalDays:
      cloneValue(
        originalDays,
      ),

    optimizedDays,

    evidence,

    actions: [
      ...(evidence
        .unscheduledStops
        .length
        ? [
            "remove-unscheduled-stops",
          ]
        : []),

      ...(evidence
        .overloadedDays
        .length
        ? [
            "reduce-high-intensity-days",
          ]
        : []),

      ...(evidence
        .longTravelDays
        .length
        ? [
            "review-long-travel-days",
          ]
        : []),
    ],
  };
}


export function optimizationChanged(
  result,
) {
  if (!result) {
    return false;
  }

  return (
    JSON.stringify(
      result.originalDays ?? [],
    ) !==
    JSON.stringify(
      result.optimizedDays ?? [],
    )
  );
}


export function countOptimizedDestinations(
  days,
) {
  if (!Array.isArray(days)) {
    return 0;
  }

  return days.reduce(
    (total, day) =>
      total +
      (
        Array.isArray(
          day?.destinations,
        )
          ? day.destinations.length
          : 0
      ),
    0,
  );
}


export function optimizationSummary(
  result,
) {
  const originalCount =
    countOptimizedDestinations(
      result?.originalDays,
    );

  const optimizedCount =
    countOptimizedDestinations(
      result?.optimizedDays,
    );

  return {
    changed:
      optimizationChanged(
        result,
      ),

    originalDestinationCount:
      originalCount,

    optimizedDestinationCount:
      optimizedCount,

    removedDestinationCount:
      Math.max(
        0,
        originalCount -
        optimizedCount,
      ),

    actionCount:
      Array.isArray(
        result?.actions,
      )
        ? result.actions.length
        : 0,
  };
}
