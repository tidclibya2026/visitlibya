import assert from "node:assert/strict";
import test from "node:test";

import {
  baseVisitDurationMinutes,
  canAddDestinationToDay,
  dailyVisitBudgetMinutes,
  totalVisitMinutes,
  visitBudgetStatus,
  visitDurationMinutes,
} from "../assets/js/app/ai/visit-duration-intelligence.js";


test("archaeology has three hour base visit duration", () => {
  assert.equal(
    baseVisitDurationMinutes({
      category_key: "archaeology",
    }),
    180,
  );
});


test("unknown category uses safe default duration", () => {
  assert.equal(
    baseVisitDurationMinutes({
      category_key: "unknown",
    }),
    120,
  );
});


test("relaxed pace increases visit duration", () => {
  const destination = {
    category_key: "heritage",
  };

  assert.ok(
    visitDurationMinutes(
      destination,
      "relaxed",
    ) >
    visitDurationMinutes(
      destination,
      "balanced",
    ),
  );
});


test("active pace reduces visit duration", () => {
  const destination = {
    category_key: "heritage",
  };

  assert.ok(
    visitDurationMinutes(
      destination,
      "active",
    ) <
    visitDurationMinutes(
      destination,
      "balanced",
    ),
  );
});


test("daily visit budgets differ by pace", () => {
  assert.equal(
    dailyVisitBudgetMinutes(
      "relaxed",
    ),
    360,
  );

  assert.equal(
    dailyVisitBudgetMinutes(
      "balanced",
    ),
    450,
  );

  assert.equal(
    dailyVisitBudgetMinutes(
      "active",
    ),
    540,
  );
});


test("totalVisitMinutes sums destinations", () => {
  const result =
    totalVisitMinutes(
      [
        {
          category_key:
            "archaeology",
        },
        {
          category_key:
            "museums",
        },
      ],
      "balanced",
    );

  assert.equal(
    result,
    300,
  );
});


test("visit budget reports remaining minutes", () => {
  const result =
    visitBudgetStatus({
      destinations: [
        {
          category_key:
            "archaeology",
        },
      ],
      pace: "balanced",
    });

  assert.equal(
    result.usedMinutes,
    180,
  );

  assert.equal(
    result.budgetMinutes,
    450,
  );

  assert.equal(
    result.remainingMinutes,
    270,
  );

  assert.equal(
    result.exceedsBudget,
    false,
  );
});


test("visit budget detects overloaded day", () => {
  const result =
    visitBudgetStatus({
      destinations: [
        {
          category_key:
            "desert-expedition",
        },
        {
          category_key:
            "archaeology",
        },
      ],
      pace: "balanced",
    });

  assert.equal(
    result.exceedsBudget,
    true,
  );
});


test("candidate can be added when day remains within budget", () => {
  assert.equal(
    canAddDestinationToDay({
      currentDestinations: [
        {
          category_key:
            "museums",
        },
      ],
      candidate: {
        category_key:
          "heritage",
      },
      pace: "balanced",
    }),
    true,
  );
});


test("candidate is rejected when day exceeds visit budget", () => {
  assert.equal(
    canAddDestinationToDay({
      currentDestinations: [
        {
          category_key:
            "desert-expedition",
        },
      ],
      candidate: {
        category_key:
          "archaeology",
      },
      pace: "balanced",
    }),
    false,
  );
});
