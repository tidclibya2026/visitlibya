const PACE_RULES = Object.freeze({
  relaxed: Object.freeze({
    maxContinuousActivityMinutes: 150,
    shortRestMinutes: 30,
    lunchStartMinutes: 12 * 60 + 30,
    lunchEndMinutes: 14 * 60 + 30,
    lunchDurationMinutes: 75,
  }),

  balanced: Object.freeze({
    maxContinuousActivityMinutes: 180,
    shortRestMinutes: 20,
    lunchStartMinutes: 12 * 60 + 30,
    lunchEndMinutes: 14 * 60,
    lunchDurationMinutes: 60,
  }),

  active: Object.freeze({
    maxContinuousActivityMinutes: 210,
    shortRestMinutes: 15,
    lunchStartMinutes: 13 * 60,
    lunchEndMinutes: 14 * 60,
    lunchDurationMinutes: 45,
  }),
});


function normalizePace(value) {
  const pace = String(value ?? "")
    .trim()
    .toLowerCase();

  if (
    pace === "relaxed" ||
    pace === "balanced" ||
    pace === "active"
  ) {
    return pace;
  }

  return "balanced";
}


export function mealRestRules(
  pace = "balanced",
) {
  return PACE_RULES[
    normalizePace(pace)
  ];
}


export function shouldInsertShortRest({
  continuousActivityMinutes,
  pace = "balanced",
}) {
  const activity =
    Number(
      continuousActivityMinutes,
    );

  if (
    !Number.isFinite(activity) ||
    activity < 0
  ) {
    return false;
  }

  return (
    activity >=
    mealRestRules(pace)
      .maxContinuousActivityMinutes
  );
}


export function lunchWindowStatus(
  currentMinutes,
  pace = "balanced",
) {
  const current =
    Number(currentMinutes);

  if (!Number.isFinite(current)) {
    return "unknown";
  }

  const rules =
    mealRestRules(pace);

  if (
    current <
    rules.lunchStartMinutes
  ) {
    return "before";
  }

  if (
    current <=
    rules.lunchEndMinutes
  ) {
    return "within";
  }

  return "after";
}


export function shouldInsertLunch({
  currentMinutes,
  lunchInserted = false,
  pace = "balanced",
}) {
  if (lunchInserted) {
    return false;
  }

  return (
    lunchWindowStatus(
      currentMinutes,
      pace,
    ) === "within"
  );
}


export function createShortRestStop({
  startsAt,
  pace = "balanced",
}) {
  const start =
    Number(startsAt);

  if (!Number.isFinite(start)) {
    return null;
  }

  const duration =
    mealRestRules(pace)
      .shortRestMinutes;

  return {
    type: "rest",
    startsAt: start,
    endsAt:
      start + duration,
    durationMinutes:
      duration,
    reason:
      "continuous-activity-limit",
  };
}


export function createLunchStop({
  startsAt,
  pace = "balanced",
}) {
  const start =
    Number(startsAt);

  if (!Number.isFinite(start)) {
    return null;
  }

  const duration =
    mealRestRules(pace)
      .lunchDurationMinutes;

  return {
    type: "meal",
    mealType: "lunch",
    startsAt: start,
    endsAt:
      start + duration,
    durationMinutes:
      duration,
    reason:
      "lunch-window",
  };
}


export function insertMealAndRestStops({
  scheduledItems,
  pace = "balanced",
}) {
  if (!Array.isArray(scheduledItems)) {
    return [];
  }

  const result = [];

  let continuousActivityMinutes = 0;
  let lunchInserted = false;

  for (const item of scheduledItems) {
    if (
      !item ||
      item.scheduled === false ||
      !Number.isFinite(
        Number(item.startsAt),
      ) ||
      !Number.isFinite(
        Number(item.endsAt),
      )
    ) {
      result.push(item);
      continue;
    }

    const startsAt =
      Number(item.startsAt);

    const endsAt =
      Number(item.endsAt);

    if (
      shouldInsertLunch({
        currentMinutes:
          startsAt,
        lunchInserted,
        pace,
      })
    ) {
      const lunch =
        createLunchStop({
          startsAt,
          pace,
        });

      if (lunch) {
        result.push(lunch);
        lunchInserted = true;

        continuousActivityMinutes = 0;
      }
    }

    if (
      shouldInsertShortRest({
        continuousActivityMinutes,
        pace,
      })
    ) {
      const rest =
        createShortRestStop({
          startsAt,
          pace,
        });

      if (rest) {
        result.push(rest);
        continuousActivityMinutes = 0;
      }
    }

    result.push(item);

    continuousActivityMinutes +=
      Math.max(
        0,
        endsAt - startsAt,
      );
  }

  return result;
}
