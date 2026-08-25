import {
  formatClockMinutes,
} from "./opening-hours-intelligence.js";

import {
  adjustedRoadTravelMinutes,
} from "./road-feasibility.js";

import {
  estimatedTravelMinutes,
} from "./travel-time-intelligence.js";

import {
  resolveTimelineConflicts,
} from "./timeline-conflict-resolution.js";


function finiteMinutes(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : null;
}


function normalizeTimelineItem(item) {
  if (!item) return null;

  return {
    ...item,

    startsAt:
      finiteMinutes(item.startsAt),

    endsAt:
      finiteMinutes(item.endsAt),
  };
}


export function buildTravelTimelineItem({
  previousDestination,
  nextDestination,
  startsAt,
}) {
  if (
    !previousDestination ||
    !nextDestination
  ) {
    return null;
  }

  const baseMinutes =
    estimatedTravelMinutes(
      previousDestination,
      nextDestination,
    );

  if (baseMinutes === null) {
    return null;
  }

  const adjustedMinutes =
    adjustedRoadTravelMinutes(
      baseMinutes,
      nextDestination,
    );

  if (adjustedMinutes === null) {
    return null;
  }

  const start =
    finiteMinutes(startsAt);

  if (start === null) {
    return null;
  }

  const duration =
    Math.max(
      0,
      Math.round(adjustedMinutes),
    );

  return {
    type: "travel",

    fromDestination:
      previousDestination,

    toDestination:
      nextDestination,

    startsAt: start,

    endsAt:
      start + duration,

    durationMinutes:
      duration,

    startsAtLabel:
      formatClockMinutes(start),

    endsAtLabel:
      formatClockMinutes(
        start + duration,
      ),
  };
}


export function sortTimelineItems(
  items,
) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .map(normalizeTimelineItem)
    .filter(Boolean)
    .sort((left, right) => {
      const leftStart =
        left.startsAt ??
        Number.POSITIVE_INFINITY;

      const rightStart =
        right.startsAt ??
        Number.POSITIVE_INFINITY;

      if (leftStart !== rightStart) {
        return leftStart - rightStart;
      }

      const priority = {
        travel: 1,
        meal: 2,
        rest: 3,
        destination: 4,
      };

      return (
        (priority[left.type] ?? 99) -
        (priority[right.type] ?? 99)
      );
    });
}


export function insertTravelBetweenDestinations(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return [];
  }

  const result = [];

  let previousDestinationItem = null;

  for (const rawItem of timeline) {
    const item =
      normalizeTimelineItem(
        rawItem,
      );

    if (!item) continue;

    if (
      item.type === "destination"
    ) {
      if (
        previousDestinationItem &&
        previousDestinationItem
          .destination &&
        item.destination
      ) {
        const travel =
          buildTravelTimelineItem({
            previousDestination:
              previousDestinationItem
                .destination,

            nextDestination:
              item.destination,

            startsAt:
              previousDestinationItem
                .endsAt,
          });

        if (travel) {
          result.push(travel);
        }
      }

      result.push(item);

      previousDestinationItem =
        item;

      continue;
    }

    result.push(item);
  }

  return sortTimelineItems(result);
}


export function unifiedDailyTimeline(
  timeline,
) {
  const withTravel =
    insertTravelBetweenDestinations(
      timeline,
    );

  const resolved =
    resolveTimelineConflicts(
      withTravel,
    );

  return resolved.map(
    (item) => ({
      ...item,

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
    }),
  );
}
