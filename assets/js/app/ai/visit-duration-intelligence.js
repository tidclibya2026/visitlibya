const CATEGORY_BASE_MINUTES = Object.freeze({
  "historic-cities": 150,
  archaeology: 180,
  heritage: 150,
  museums: 120,
  culture: 120,
  "mountains-nature": 180,
  nature: 180,
  coast: 150,
  "mediterranean-coast": 150,
  oases: 150,
  desert: 240,
  "desert-expedition": 300,
});

const PACE_MULTIPLIERS = Object.freeze({
  relaxed: 1.15,
  balanced: 1,
  active: 0.85,
});

const DAILY_VISIT_BUDGET_MINUTES = Object.freeze({
  relaxed: 360,
  balanced: 450,
  active: 540,
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


export function baseVisitDurationMinutes(
  destination,
) {
  const category =
    normalize(
      destination?.category_key,
    );

  return (
    CATEGORY_BASE_MINUTES[category] ??
    120
  );
}


export function visitDurationMinutes(
  destination,
  pace = "balanced",
) {
  const base =
    baseVisitDurationMinutes(
      destination,
    );

  const multiplier =
    PACE_MULTIPLIERS[
      normalizePace(pace)
    ];

  return Math.round(
    base * multiplier,
  );
}


export function dailyVisitBudgetMinutes(
  pace = "balanced",
) {
  return DAILY_VISIT_BUDGET_MINUTES[
    normalizePace(pace)
  ];
}


export function totalVisitMinutes(
  destinations,
  pace = "balanced",
) {
  if (!Array.isArray(destinations)) {
    return 0;
  }

  return destinations.reduce(
    (total, destination) =>
      total +
      visitDurationMinutes(
        destination,
        pace,
      ),
    0,
  );
}


export function visitBudgetStatus({
  destinations,
  pace = "balanced",
}) {
  const usedMinutes =
    totalVisitMinutes(
      destinations,
      pace,
    );

  const budgetMinutes =
    dailyVisitBudgetMinutes(
      pace,
    );

  return {
    usedMinutes,
    budgetMinutes,
    remainingMinutes:
      Math.max(
        0,
        budgetMinutes -
        usedMinutes,
      ),
    exceedsBudget:
      usedMinutes >
      budgetMinutes,
  };
}


export function canAddDestinationToDay({
  currentDestinations,
  candidate,
  pace = "balanced",
}) {
  const destinations = [
    ...(Array.isArray(
      currentDestinations,
    )
      ? currentDestinations
      : []),
    candidate,
  ].filter(Boolean);

  return !visitBudgetStatus({
    destinations,
    pace,
  }).exceedsBudget;
}
