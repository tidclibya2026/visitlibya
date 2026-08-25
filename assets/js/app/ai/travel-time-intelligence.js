import {
  distanceKm,
} from "./coordinate-routing.js";


const DEFAULT_SPEED_KMH = 65;

const PACE_DAILY_TRAVEL_LIMITS = Object.freeze({
  relaxed: 180,
  balanced: 300,
  active: 450,
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


export function estimatedTravelMinutes(
  source,
  target,
  {
    averageSpeedKmh = DEFAULT_SPEED_KMH,
  } = {},
) {
  const distance =
    distanceKm(source, target);

  const speed =
    Number(averageSpeedKmh);

  if (
    distance === null ||
    !Number.isFinite(speed) ||
    speed <= 0
  ) {
    return null;
  }

  return (
    distance /
    speed *
    60
  );
}


export function dailyTravelBudgetMinutes(
  pace,
) {
  const normalized =
    normalizePace(pace);

  return PACE_DAILY_TRAVEL_LIMITS[
    normalized
  ];
}


export function travelTimeBand(
  minutes,
) {
  if (
    minutes === null ||
    !Number.isFinite(minutes)
  ) {
    return "unknown";
  }

  if (minutes <= 90) {
    return "short";
  }

  if (minutes <= 180) {
    return "moderate";
  }

  if (minutes <= 360) {
    return "long";
  }

  return "very-long";
}


export function travelTimePenalty({
  source,
  target,
  pace = "balanced",
  days = 1,
}) {
  const minutes =
    estimatedTravelMinutes(
      source,
      target,
    );

  if (minutes === null) {
    return {
      minutes: null,
      band: "unknown",
      penalty: 0,
      exceedsDailyBudget: false,
    };
  }

  const budget =
    dailyTravelBudgetMinutes(
      pace,
    );

  const exceedsDailyBudget =
    minutes > budget;

  const band =
    travelTimeBand(minutes);

  let penalty = 0;

  if (band === "moderate") {
    penalty = 5;
  }

  if (band === "long") {
    penalty =
      Number(days) <= 3
        ? 35
        : 15;
  }

  if (band === "very-long") {
    if (Number(days) <= 3) {
      penalty = 90;
    } else if (Number(days) <= 6) {
      penalty = 55;
    } else {
      penalty = 25;
    }
  }

  if (exceedsDailyBudget) {
    penalty += 15;
  }

  return {
    minutes,
    band,
    penalty,
    exceedsDailyBudget,
  };
}


export function requiresTravelTimeDay({
  source,
  target,
  pace = "balanced",
}) {
  const minutes =
    estimatedTravelMinutes(
      source,
      target,
    );

  if (minutes === null) {
    return null;
  }

  const budget =
    dailyTravelBudgetMinutes(
      pace,
    );

  return minutes > budget;
}
