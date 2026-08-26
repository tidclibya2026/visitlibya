# Phase 3.1 planner execution parity

The backend core is intentionally route-independent. A caller must load each
destination through `PlannerDestinationAuthorityService`, pass its serialized
`PlannerDestinationAuthority` value to `normalize_destination`, and then call
`execute_planner`. The executor never reads destination tables or profiles
directly and never changes publication or verification state.

| JavaScript source/function | Python equivalent | Status |
| --- | --- | --- |
| `planner-authority-adapter.js` / `applyPlannerProfile` | `normalize_destination` | Parity; authority state preserved |
| `geographic-intelligence.js` / region and penalty functions | `destination_region`, `region_relationship`, `geographic_penalty` | Parity |
| `trip-planner-engine.js` / interest, traveler, and destination scoring | `score_destination`, `rank_destinations` | Parity for execution-affecting fields |
| `coordinate-routing.js` / coordinate distance and nearest order | `valid_coordinates`, `distance_km`, `order_nearest` | Parity |
| `route-sequencing.js` / corridor order | `route_order` | Parity |
| `travel-time-intelligence.js` / travel estimate and penalty | `estimated_travel_minutes`, `travel_time_penalty` | Parity |
| `travel-day-planner.js` and engine day allocation | `execute_planner` allocation stage | Parity |
| `road-feasibility.js` / access evidence | `road_profile`, `score_destination` | Parity |
| `visit-duration-intelligence.js` / duration and budget | `visit_duration_minutes`, `rebuild_visit_day` | Parity |
| `opening-hours-intelligence.js` / sequence scheduling | `schedule_destinations` | Parity |
| `meal-rest-intelligence.js` / break insertion | `insert_meal_rest` | Parity |
| `timeline-conflict-resolution.js` / conflict shifting | `resolve_timeline_conflicts` | Parity |
| `unified-daily-timeline.js` / travel insertion and timeline | `build_timeline` | Parity |
| `daily-summary-intelligence.js` / summary and intensity | `daily_summary` | Parity |
| `trip-feasibility-score.js` / evidence, penalty, messages | `trip_feasibility` | Parity |
| `trip-recommendation-insights.js` / evidence and recommendations | `recommendations` | Parity |
| `trip-auto-optimization.js` / structural optimization | `optimize` | Parity |
| `trip-optimization-evaluation.js` / rebuild and comparison | `rebuild_visit_day`, `rebuild_days`, `evaluate_optimization` | Parity |
| `trip-planner-engine.js` / `buildSuggestedItinerary` | `execute_planner` | Integrated projected-output parity |

## Remaining intentional differences

- Day-specific opening-hours calendars and timezone/date evaluation are not in
  the current JavaScript execution path and are not introduced here.
- Python uses ordinary Unicode code-point ordering for the stable slug
  tiebreaker. Current ASCII destination slugs match JavaScript `localeCompare`;
  locale-sensitive non-ASCII slug ordering is intentionally unsupported.
- The Python public result omits the JavaScript engine's nested `preferences`
  echo because the typed backend result does not expose it yet. This does not
  affect planning decisions or persisted authority state.

Golden fixtures are generated only from existing JavaScript modules by
`backend/tests/fixtures/generate_planner_parity.mjs`; tests have no network or
external API dependency.

Phase 3.2 whole-pipeline goldens use only
`PlannerDestinationAuthorityService`-shaped records and compare integrated
Python output against `generate_planner_full_parity.mjs` for ranking,
allocation, conflicts, evidence, recommendations, optimization, and explicit
unverified-state preservation.
