import {
  dailyVisitBudgetMinutes,
  visitBudgetStatus,
  visitDurationMinutes,
} from "./visit-duration-intelligence.js";

import {
  formatClockMinutes,
  scheduleDestinationSequence,
} from "./opening-hours-intelligence.js";

import {
  insertMealAndRestStops,
} from "./meal-rest-intelligence.js";

import {
  unifiedDailyTimeline,
} from "./unified-daily-timeline.js";

import {
  dailySummary,
  dayIntensity,
} from "./daily-summary-intelligence.js";

import {
  tripFeasibility,
} from "./trip-feasibility-score.js";

import {
  countOptimizedDestinations,
} from "./trip-auto-optimization.js";


function cloneValue(value) {
  return JSON.parse(
    JSON.stringify(value),
  );
}


function safeDays(days) {
  return Array.isArray(days)
    ? days
    : [];
}


function rebuildTravelDay(
  day,
  pace,
) {
  const budget =
    dailyVisitBudgetMinutes(
      pace,
    );

  return {
    ...cloneValue(day),

    visitBudget: {
      usedMinutes: 0,
      budgetMinutes: budget,
      remainingMinutes: budget,
      exceedsBudget: false,
    },

    timeline:
      Array.isArray(day?.timeline)
        ? cloneValue(day.timeline)
        : [],

    summary:
      day?.summary
        ? cloneValue(day.summary)
        : {
            stopCount: 0,
            visitMinutes: 0,
            travelMinutes: 0,
            mealMinutes: 0,
            restMinutes: 0,
            startsAt: null,
            endsAt: null,
            totalDayMinutes: 0,
            activityMinutes: 0,
            recoveryMinutes: 0,
            intensity: "unknown",
          },
  };
}


export function rebuildOptimizedVisitDay(
  day,
  preferences = {},
) {
  const pace =
    preferences.pace ??
    "balanced";

  const copy =
    cloneValue(
      day ?? {},
    );

  const destinations =
    Array.isArray(
      copy.destinations,
    )
      ? copy.destinations
      : [];

  copy.destinations =
    destinations.map(
      (destination) => ({
        ...destination,

        planner_score: {
          ...(
            destination
              .planner_score ?? {}
          ),

          estimatedVisitMinutes:
            visitDurationMinutes(
              destination,
              pace,
            ),
        },
      }),
    );

  copy.visitBudget =
    visitBudgetStatus({
      destinations:
        copy.destinations,
      pace,
    });

  const scheduledDestinations =
    scheduleDestinationSequence({
      destinations:
        copy.destinations,

      pace,

      visitDurationResolver:
        (destination) =>
          visitDurationMinutes(
            destination,
            pace,
          ),
    });

  copy.destinations =
    scheduledDestinations.map(
      (scheduledItem) => ({
        ...scheduledItem.destination,

        planner_score: {
          ...(
            scheduledItem
              .destination
              .planner_score ?? {}
          ),

          scheduled:
            scheduledItem.scheduled,

          scheduledStartMinutes:
            scheduledItem.startsAt,

          scheduledEndMinutes:
            scheduledItem.endsAt,

          scheduledStart:
            scheduledItem.startsAt ===
            null
              ? null
              : formatClockMinutes(
                  scheduledItem
                    .startsAt,
                ),

          scheduledEnd:
            scheduledItem.endsAt ===
            null
              ? null
              : formatClockMinutes(
                  scheduledItem
                    .endsAt,
                ),

          openingHoursStatus:
            scheduledItem
              .openingStatus,

          scheduleReason:
            scheduledItem.reason,
        },
      }),
    );

  const mealRestTimeline =
    insertMealAndRestStops({
      scheduledItems:
        scheduledDestinations,

      pace,
    }).map((item) => {
      if (
        item?.type === "meal" ||
        item?.type === "rest"
      ) {
        return item;
      }

      return {
        type: "destination",

        destination:
          item.destination,

        scheduled:
          item.scheduled,

        reason:
          item.reason,

        openingStatus:
          item.openingStatus,

        startsAt:
          item.startsAt,

        endsAt:
          item.endsAt,
      };
    });

  copy.timeline =
    unifiedDailyTimeline(
      mealRestTimeline,
    );

  const summary =
    dailySummary(
      copy.timeline,
    );

  copy.summary = {
    ...summary,

    intensity:
      dayIntensity(
        summary,
      ),
  };

  return copy;
}


export function rebuildOptimizedDays(
  days,
  preferences = {},
) {
  const pace =
    preferences.pace ??
    "balanced";

  return safeDays(days).map(
    (day) =>
      day?.type === "travel"
        ? rebuildTravelDay(
            day,
            pace,
          )
        : rebuildOptimizedVisitDay(
            day,
            preferences,
          ),
  );
}


export function evaluateOptimization({
  originalDays,
  optimizedDays,
  preferences = {},
} = {}) {
  const beforeDays =
    safeDays(
      originalDays,
    );

  const afterDays =
    rebuildOptimizedDays(
      optimizedDays,
      preferences,
    );

  const beforeFeasibility =
    tripFeasibility({
      days: beforeDays,
    });

  const afterFeasibility =
    tripFeasibility({
      days: afterDays,
    });

  const scoreDelta =
    afterFeasibility.score -
    beforeFeasibility.score;

  return {
    before: {
      days:
        cloneValue(
          beforeDays,
        ),

      feasibility:
        beforeFeasibility,

      destinationCount:
        countOptimizedDestinations(
          beforeDays,
        ),
    },

    after: {
      days:
        afterDays,

      feasibility:
        afterFeasibility,

      destinationCount:
        countOptimizedDestinations(
          afterDays,
        ),
    },

    improvement: {
      scoreDelta,

      improved:
        scoreDelta > 0,

      unchanged:
        scoreDelta === 0,

      worsened:
        scoreDelta < 0,
    },
  };
}
