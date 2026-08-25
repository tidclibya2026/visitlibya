import {
  timelineItemDuration,
} from "./timeline-conflict-resolution.js";


function finiteMinutes(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : null;
}


function sumDurationByType(
  timeline,
  type,
) {
  if (!Array.isArray(timeline)) {
    return 0;
  }

  return timeline
    .filter(
      (item) =>
        item?.type === type,
    )
    .reduce(
      (total, item) => {
        const duration =
          timelineItemDuration(
            item,
          );

        return total +
          (
            Number.isFinite(
              duration,
            )
              ? duration
              : 0
          );
      },
      0,
    );
}


function firstTimedItem(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return null;
  }

  return (
    timeline.find(
      (item) =>
        finiteMinutes(
          item?.startsAt,
        ) !== null,
    ) ?? null
  );
}


function lastTimedItem(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return null;
  }

  const timed =
    timeline.filter(
      (item) =>
        finiteMinutes(
          item?.endsAt,
        ) !== null,
    );

  return timed.length
    ? timed[timed.length - 1]
    : null;
}


export function dailyStopCount(
  timeline,
) {
  if (!Array.isArray(timeline)) {
    return 0;
  }

  return timeline.filter(
    (item) =>
      item?.type ===
      "destination",
  ).length;
}


export function dailySummary(
  timeline,
) {
  const safeTimeline =
    Array.isArray(timeline)
      ? timeline
      : [];

  const first =
    firstTimedItem(
      safeTimeline,
    );

  const last =
    lastTimedItem(
      safeTimeline,
    );

  const startsAt =
    finiteMinutes(
      first?.startsAt,
    );

  const endsAt =
    finiteMinutes(
      last?.endsAt,
    );

  const totalDayMinutes =
    startsAt !== null &&
    endsAt !== null &&
    endsAt >= startsAt
      ? endsAt - startsAt
      : 0;

  const visitMinutes =
    sumDurationByType(
      safeTimeline,
      "destination",
    );

  const travelMinutes =
    sumDurationByType(
      safeTimeline,
      "travel",
    );

  const mealMinutes =
    sumDurationByType(
      safeTimeline,
      "meal",
    );

  const restMinutes =
    sumDurationByType(
      safeTimeline,
      "rest",
    );

  return {
    stopCount:
      dailyStopCount(
        safeTimeline,
      ),

    visitMinutes,
    travelMinutes,
    mealMinutes,
    restMinutes,

    startsAt,
    endsAt,

    totalDayMinutes,

    activityMinutes:
      visitMinutes +
      travelMinutes,

    recoveryMinutes:
      mealMinutes +
      restMinutes,
  };
}


export function dayIntensity(
  summary,
) {
  const activityMinutes =
    Number(
      summary?.activityMinutes ??
      0,
    );

  const recoveryMinutes =
    Number(
      summary?.recoveryMinutes ??
      0,
    );

  const totalDayMinutes =
    Number(
      summary?.totalDayMinutes ??
      0,
    );

  if (
    totalDayMinutes <= 0
  ) {
    return "unknown";
  }

  if (
    activityMinutes >= 480 &&
    recoveryMinutes < 60
  ) {
    return "high";
  }

  if (
    activityMinutes >= 330
  ) {
    return "moderate";
  }

  return "light";
}
