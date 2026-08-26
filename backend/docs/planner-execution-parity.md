# Phase 3.1 planner execution parity

The backend core is intentionally route-independent. A caller must load each
destination through `PlannerDestinationAuthorityService`, pass its serialized
`PlannerDestinationAuthority` value to `normalize_destination`, and then call
`execute_planner`. The executor never reads destination tables or profiles
directly and never changes publication or verification state.

| JavaScript reference | Python backend equivalent |
| --- | --- |
| `planner-authority-adapter.js` / `applyPlannerProfile` | `normalize_destination` |
| `coordinate-routing.js` / `validCoordinates`, `distanceKm` | `valid_coordinates`, `distance_km` |
| `travel-time-intelligence.js` / `estimatedTravelMinutes` | `estimated_travel_minutes` |
| `road-feasibility.js` / `destinationAccessProfile` | `road_profile` |
| `visit-duration-intelligence.js` / `visitDurationMinutes` | `visit_duration_minutes` |
| `opening-hours-intelligence.js` / `scheduleDestinationSequence` | `schedule_destinations` |
| `meal-rest-intelligence.js` / `insertMealAndRestStops` | `insert_meal_rest` |
| `unified-daily-timeline.js` / `unifiedDailyTimeline` | `build_timeline` |
| `daily-summary-intelligence.js` / `dailySummary`, `dayIntensity` | `daily_summary` |
| `trip-feasibility-score.js` / `tripFeasibility` | `trip_feasibility` |
| `trip-recommendation-insights.js` / `buildTripRecommendations` | `recommendations` |
| `trip-auto-optimization.js` / structural optimization | `optimize` |
| `trip-planner-engine.js` / `buildSuggestedItinerary` | `execute_planner` |

## Deliberate Phase 3.1 gaps

- Geographic region classification, interest/traveler scoring, and full route
  selection remain JavaScript-reference behavior; Python currently orders
  authorized inputs by planner priority and stable slug.
- Python timeline travel insertion is deterministic but does not yet port the
  JavaScript conflict-resolution and optimized-day rebuild stages.
- Feasibility and recommendation output is a minimal stable subset. Full
  evidence/message parity and optimization before/after evaluation are Phase
  3.2 work.
- Day-specific opening-hours calendars and timezone/date evaluation are not in
  the current JavaScript execution path and are not introduced here.

Golden fixtures are generated only from existing JavaScript modules by
`backend/tests/fixtures/generate_planner_parity.mjs`; tests have no network or
external API dependency.
