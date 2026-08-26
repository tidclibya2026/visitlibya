# Planner governance and telemetry

Three states are independent and must never be inferred from one another:

- Destination publication status controls whether canonical editorial place content is public.
- DestinationPlannerProfile verification status records review confidence in operational planner data.
- PlannerRun acceptance status records a user's decision about one generated itinerary version.

A published destination can have no planner profile. A verified profile cannot publish a draft
destination. Accepting a PlannerRun cannot verify a profile or publish any destination.

## Authority boundaries

`Destination` owns canonical identity, coordinates, municipality, region, category, translations,
editorial priority, activity, and publication state. `DestinationPlannerProfile` owns structured
visit duration, opening hours, access, roads, operational priority, and stop-suitability data.
`PlannerRun` owns execution versions and input, itinerary, feasibility, recommendation, and
optimization evidence. Frontend JavaScript is deterministic reference/fallback intelligence, not
the long-term production authority.

## Audit and telemetry

The request middleware supplies or generates a validated request ID and logs method, route, status,
and duration. Planner mutations emit structured `visitlibya.planner.audit` events containing only
the event, actor ID, request ID, resource IDs, lifecycle status, and profile verification status.
Snapshots, tokens, credentials, and planner evidence bodies are deliberately excluded. These logs
support request/status counts, planner create/accept/reject events, failures through HTTP status logs,
and correlation without introducing a metrics platform.

Static/frontend fallback cannot be counted authoritatively by the backend because no request may
reach it. The frontend emits a debug-only fallback diagnostic when configured; production fallback
measurement requires an approved privacy-aware client telemetry design and is not implemented here.
