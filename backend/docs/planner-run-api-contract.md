# Visit Libya Planner Run API Contract

Status: Phase 2.3
Authority: Backend
Persistence: PostgreSQL/PostGIS
Entity: PlannerRun

## Purpose

PlannerRun represents one authoritative execution record of the Visit Libya AI Trip Planner.

Each run preserves:

- planner input
- generated itinerary
- feasibility evidence
- recommendations
- optimization evidence
- planner version
- engine version
- lifecycle status

The frontend AI planner remains the deterministic reference implementation while backend authority and persistence are migrated incrementally.

---

## Lifecycle

Allowed lifecycle transitions:

GENERATED -> ACCEPTED
GENERATED -> REJECTED
ACCEPTED -> SUPERSEDED

Terminal states:

REJECTED
SUPERSEDED

Rules:

- A rejected run cannot be accepted.
- A superseded run cannot be accepted.
- An accepted run cannot be rejected.
- Accepting a trip-bound run supersedes other GENERATED or ACCEPTED runs for the same trip and owner.
- Clients must not directly set SUPERSEDED.
- Lifecycle actions must be controlled by backend service rules.

---

## Authentication and ownership

All PlannerRun endpoints are authenticated.

A user may only:

- create runs owned by that user
- read runs owned by that user
- update evidence for runs owned by that user
- accept runs owned by that user
- reject runs owned by that user

If trip_id is supplied during creation, the backend must verify that the trip belongs to the authenticated user before persistence.

Ownership must never be trusted from request payloads.

user_id is derived from authentication context.

---

## Create Planner Run

POST /planner-runs

Request:

PlannerRunCreate

Fields:

- trip_id: optional positive integer
- planner_version: positive integer
- engine_version: non-empty string
- feasibility_score: optional integer from 0 to 100
- input_snapshot: object
- itinerary_snapshot: object
- feasibility_snapshot: object
- recommendations_snapshot: object
- optimization_snapshot: object

Backend-generated fields:

- id
- user_id
- status = GENERATED
- created_at
- updated_at

Response:

201 Created

PlannerRunResponse

---

## Get Planner Run

GET /planner-runs/{planner_run_id}

Response:

200 OK

PlannerRunResponse

Ownership is required.

If no owned run exists:

404 Not Found

---

## List User Planner Runs

GET /planner-runs?skip=0&limit=50

Rules:

- skip >= 0
- 1 <= limit <= 100

Response:

200 OK

A paginated PlannerRunSummaryResponse collection.

Ordering:

created_at DESC
id DESC

---

## List Planner Runs for Trip

GET /trips/{trip_id}/planner-runs?skip=0&limit=50

Ownership of the trip is required.

Response:

200 OK

PlannerRunSummaryResponse collection.

Ordering:

created_at DESC
id DESC

---

## Latest Planner Run for Trip

GET /trips/{trip_id}/planner-runs/latest

Response:

200 OK

PlannerRunResponse

If none exists:

404 Not Found

---

## Latest Accepted Planner Run for Trip

GET /trips/{trip_id}/planner-runs/latest-accepted

Response:

200 OK

PlannerRunResponse

If none exists:

404 Not Found

---

## Accept Planner Run

POST /planner-runs/{planner_run_id}/accept

Allowed source state:

GENERATED

Idempotent source state:

ACCEPTED

Rejected transitions:

REJECTED -> ACCEPTED
SUPERSEDED -> ACCEPTED

For a trip-bound run, acceptance must supersede other GENERATED or ACCEPTED runs belonging to the same trip and user.

The acceptance operation and supersede operation must occur in one service-owned database transaction.

Response:

200 OK

PlannerRunResponse

---

## Reject Planner Run

POST /planner-runs/{planner_run_id}/reject

Allowed source state:

GENERATED

Idempotent source state:

REJECTED

Rejected transitions:

ACCEPTED -> REJECTED
SUPERSEDED -> REJECTED

Response:

200 OK

PlannerRunResponse

---

## Update Planner Evidence

PATCH /planner-runs/{planner_run_id}/evidence

Request:

PlannerRunEvidenceUpdate

Fields:

- feasibility_score
- feasibility_snapshot
- recommendations_snapshot
- optimization_snapshot

Allowed states:

GENERATED
ACCEPTED

Rejected states:

REJECTED
SUPERSEDED

Response:

200 OK

PlannerRunResponse

---

## HTTP Error Contract

400 Bad Request

Used for invalid lifecycle transitions or invalid business parameters.

401 Unauthorized

Used when authentication is missing or invalid.

404 Not Found

Used when the PlannerRun or owned Trip does not exist for the authenticated user.

409 Conflict

Reserved for authoritative concurrency conflicts when planner-run locking/version enforcement is introduced.

422 Unprocessable Entity

Used for Pydantic request validation failures.

500 Internal Server Error

Persistence failures must be mapped through backend domain exceptions rather than exposing database exceptions.

---

## Authority Boundary

Frontend:

- collects planner preferences
- renders planner results
- may continue using deterministic JavaScript planner during migration
- must not become authoritative persistence

Backend:

- authenticates ownership
- controls PlannerRun lifecycle
- validates trip ownership
- persists planner evidence
- owns transactions
- exposes authoritative planner APIs

Database:

- PostgreSQL/PostGIS is the production system of record
- PlannerRun snapshots preserve decision evidence and reproducibility context

---

## Deferred to later phases

Not part of Phase 2.3:

- FastAPI router implementation
- planner execution endpoint
- authoritative destination planner profile
- opening-hours authority
- frontend API migration
- planner-run concurrency locking
- telemetry and audit events

These are implemented in later backend authority phases.
