const DEFAULT_DAY_START_MINUTES = Object.freeze({
  relaxed: 10 * 60,
  balanced: 9 * 60,
  active: 8 * 60,
});

const DEFAULT_DAY_END_MINUTES = Object.freeze({
  relaxed: 18 * 60,
  balanced: 18 * 60,
  active: 19 * 60,
});


function normalize(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}


function normalizePace(value) {
  const pace = normalize(value);

  if (
    pace === "relaxed" ||
    pace === "balanced" ||
    pace === "active"
  ) {
    return pace;
  }

  return "balanced";
}


export function parseClockMinutes(
  value,
) {
  if (
    typeof value !== "string"
  ) {
    return null;
  }

  const match =
    value.trim().match(
      /^([01]\d|2[0-3]):([0-5]\d)$/,
    );

  if (!match) {
    return null;
  }

  return (
    Number(match[1]) * 60 +
    Number(match[2])
  );
}


export function formatClockMinutes(
  minutes,
) {
  const value =
    Number(minutes);

  if (
    !Number.isFinite(value) ||
    value < 0 ||
    value >= 24 * 60
  ) {
    return null;
  }

  const hours =
    Math.floor(value / 60);

  const remainder =
    value % 60;

  return [
    String(hours)
      .padStart(2, "0"),
    String(remainder)
      .padStart(2, "0"),
  ].join(":");
}


export function destinationOpeningWindow(
  destination,
) {
  const openingTime =
    destination?.opening_time ??
    destination?.openingTime ??
    null;

  const closingTime =
    destination?.closing_time ??
    destination?.closingTime ??
    null;

  const opensAt =
    parseClockMinutes(
      openingTime,
    );

  const closesAt =
    parseClockMinutes(
      closingTime,
    );

  if (
    opensAt === null ||
    closesAt === null ||
    closesAt <= opensAt
  ) {
    return {
      status: "unknown",
      opensAt: null,
      closesAt: null,
    };
  }

  return {
    status: "known",
    opensAt,
    closesAt,
  };
}


export function defaultDayWindow(
  pace = "balanced",
) {
  const normalized =
    normalizePace(pace);

  return {
    startsAt:
      DEFAULT_DAY_START_MINUTES[
        normalized
      ],

    endsAt:
      DEFAULT_DAY_END_MINUTES[
        normalized
      ],
  };
}


export function canScheduleVisit({
  destination,
  arrivalMinutes,
  visitMinutes,
}) {
  const arrival =
    Number(arrivalMinutes);

  const duration =
    Number(visitMinutes);

  if (
    !Number.isFinite(arrival) ||
    !Number.isFinite(duration) ||
    duration < 0
  ) {
    return {
      schedulable: false,
      reason: "invalid-time",
      startsAt: null,
      endsAt: null,
      openingStatus: "unknown",
    };
  }

  const openingWindow =
    destinationOpeningWindow(
      destination,
    );

  if (
    openingWindow.status ===
    "unknown"
  ) {
    return {
      schedulable: true,
      reason:
        "opening-hours-unknown",
      startsAt: arrival,
      endsAt:
        arrival + duration,
      openingStatus: "unknown",
    };
  }

  const startsAt =
    Math.max(
      arrival,
      openingWindow.opensAt,
    );

  const endsAt =
    startsAt + duration;

  if (
    endsAt >
    openingWindow.closesAt
  ) {
    return {
      schedulable: false,
      reason:
        "insufficient-opening-window",
      startsAt,
      endsAt,
      openingStatus: "known",
    };
  }

  return {
    schedulable: true,
    reason: "scheduled",
    startsAt,
    endsAt,
    openingStatus: "known",
  };
}


export function scheduleDestinationSequence({
  destinations,
  pace = "balanced",
  visitDurationResolver,
}) {
  if (
    !Array.isArray(destinations)
  ) {
    return [];
  }

  if (
    typeof visitDurationResolver !==
    "function"
  ) {
    throw new TypeError(
      "visitDurationResolver is required",
    );
  }

  const dayWindow =
    defaultDayWindow(pace);

  let cursor =
    dayWindow.startsAt;

  const scheduled = [];

  for (const destination of destinations) {
    const visitMinutes =
      Number(
        visitDurationResolver(
          destination,
          pace,
        ),
      );

    const decision =
      canScheduleVisit({
        destination,
        arrivalMinutes: cursor,
        visitMinutes,
      });

    if (
      decision.schedulable &&
      decision.endsAt <=
        dayWindow.endsAt
    ) {
      scheduled.push({
        destination,
        scheduled: true,
        reason:
          decision.reason,
        openingStatus:
          decision.openingStatus,
        startsAt:
          decision.startsAt,
        endsAt:
          decision.endsAt,
        visitMinutes,
      });

      cursor =
        decision.endsAt;

      continue;
    }

    scheduled.push({
      destination,
      scheduled: false,
      reason:
        decision.schedulable
          ? "outside-daily-window"
          : decision.reason,
      openingStatus:
        decision.openingStatus,
      startsAt:
        decision.startsAt,
      endsAt:
        decision.endsAt,
      visitMinutes,
    });
  }

  return scheduled;
}
