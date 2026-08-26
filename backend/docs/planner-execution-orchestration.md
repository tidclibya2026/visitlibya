# Backend planner execution orchestration

Phase 3.3 adds an authenticated orchestration boundary without moving planning
rules into FastAPI or granting publication authority to planner data.

```text
Frontend / authenticated API
  -> POST /api/v1/trips/{trip_id}/planner-runs/execute
  -> PlannerExecutionService
       1. PlannerRunService.require_owned_trip
       2. PlannerDestinationAuthorityService.get_authority / get_authority_by_slug
       3. app.planner.execution.execute_planner
       4. PlannerRunService.create_run -> PlannerRunRepository
       5. allowlisted planner audit telemetry
```

## Contract

The request accepts unique `destination_ids` and/or `destination_slugs`, plus
`days`, `pace`, `starting_point`, `interests`, and `traveler_type`. Empty
destination sets, duplicate identifiers, invalid pace/day values, unknown
destinations, and unavailable destinations are rejected deterministically.

The response contains the generated `PlannerRun`, the deterministic planner
result, and the complete authority records used for execution. Profile states
(`verified`, `reviewed`, `unverified`, or `missing`) are returned and persisted
without promotion or inference.

## Ownership and governance

Trip ownership is checked before destination resolution. Non-owned and missing
trips share the existing not-found behavior. Every destination is resolved by
`PlannerDestinationAuthorityService`; the orchestrator never reads destination
or profile tables directly. Only active, published destinations may execute,
while their planner profiles may retain any governed verification state.

Execution creates a `generated` run. Acceptance and rejection remain separate
existing endpoints and audit events. No execution path auto-accepts or
supersedes runs.

## Persistence and audit

The input snapshot stores normalized preferences, requested identifiers, and
the serialized authority records. Output is stored in the existing itinerary,
feasibility, recommendation, and optimization snapshot columns using planner
version `1` and engine version `visitlibya-python-planner-v1`. No migration is
required.

After persistence, `planner_run_executed` is emitted through the existing
allowlisted audit logger with actor, request, run, trip, and generated status
identifiers only. Request headers, credentials, secrets, and snapshot bodies
are never passed to audit telemetry.

The JavaScript planner remains unchanged as the frontend fallback/reference.
