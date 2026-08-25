import {
  formatClockMinutes,
} from "./opening-hours-intelligence.js";


function finiteMinutes(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : null;
}


export function timelineItemDuration(
  item,
) {
  const explicit =
    finiteMinutes(
      item?.durationMinutes,
    );

  if (
    explicit !== null &&
    explicit >= 0
  ) {
    return explicit;
  }

  const startsAt =
    finiteMinutes(
      item?.startsAt,
    );

  const endsAt =
    finiteMinutes(
      item?.endsAt,
    );

  if (
    startsAt === null ||
    endsAt === null ||
    endsAt < startsAt
  ) {
    return null;
  }

  return endsAt - startsAt;
}


export function timelineHasConflict(
  previousItem,
  nextItem,
) {
  const previousEnd =
    finiteMinutes(
      previousItem?.endsAt,
    );

  const nextStart =
    finiteMinutes(
      nextItem?.startsAt,
    );

  if (
    previousEnd === null ||
    nextStart === null
  ) {
    return false;
  }

  return nextStart < previousEnd;
}


export function shiftTimelineItem(
  item,
  startsAt,
) {
  const start =
    finiteMinutes(startsAt);

  const duration =
    timelineItemDuration(
      item,
    );

  if (
    start === null ||
    duration === null
  ) {
    return {
      ...item,
    };
  }

  const end =
    start + duration;

  return {
    ...item,

    startsAt: start,
    endsAt: end,

    startsAtLabel:
      formatClockMinutes(
        start,
      ),

    endsAtLabel:
      formatClockMinutes(
        end,
      ),

    conflictAdjusted: true,
  };
}


export function resolveTimelineConflicts(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return [];
  }

  const resolved = [];

  let cursor = null;

  for (const rawItem of timeline) {
    if (!rawItem) {
      continue;
    }

    const startsAt =
      finiteMinutes(
        rawItem.startsAt,
      );

    const endsAt =
      finiteMinutes(
        rawItem.endsAt,
      );

    if (
      startsAt === null ||
      endsAt === null
    ) {
      resolved.push({
        ...rawItem,
      });

      continue;
    }

    if (
      cursor !== null &&
      startsAt < cursor
    ) {
      const shifted =
        shiftTimelineItem(
          rawItem,
          cursor,
        );

      resolved.push(
        shifted,
      );

      cursor =
        finiteMinutes(
          shifted.endsAt,
        );

      continue;
    }

    const item = {
      ...rawItem,

      startsAtLabel:
        formatClockMinutes(
          startsAt,
        ),

      endsAtLabel:
        formatClockMinutes(
          endsAt,
        ),

      conflictAdjusted:
        false,
    };

    resolved.push(item);

    cursor = endsAt;
  }

  return resolved;
}


export function timelineIsConflictFree(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return true;
  }

  const timedItems =
    timeline.filter(
      (item) =>
        finiteMinutes(
          item?.startsAt,
        ) !== null &&
        finiteMinutes(
          item?.endsAt,
        ) !== null,
    );

  for (
    let index = 1;
    index < timedItems.length;
    index += 1
  ) {
    if (
      timelineHasConflict(
        timedItems[index - 1],
        timedItems[index],
      )
    ) {
      return false;
    }
  }

  return true;
}
