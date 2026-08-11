# Development destination import

This development-only tool validates and plans a small bilingual destination catalogue before any database write. Its canonical source is `data/dev/destinations.json`; the records come from Visit Libya's reviewed curated frontend catalogue. Coordinates and database media are intentionally absent because the repository does not contain authoritative coordinate provenance or complete media-rights metadata for these records.

## Safety model

- The default mode is dry-run and ends with a rollback.
- Writes require `--apply` and `APP_ENV=development` or `APP_ENV=test`.
- Staging and production are always rejected.
- Existing rows are matched only by exact category `code` and destination `slug`.
- Existing differences are reported at field level and never overwritten.
- The complete dataset is validated before database access.
- Apply is one transaction; any error rolls back every staged row.
- The tool never deletes rows, runs migrations, resets sequences, or touches users and trips.

## Source contract

The UTF-8 JSON envelope has `schema_version`, `dataset`, `categories`, and `records`. Version 1 accepts at most 100 destinations and reuses the application schemas for category codes, destination slugs, translation lengths, publication status, and coordinate ranges. Arabic and English locale identifiers are explicit; translations are never inferred.

Coordinates must be either a complete finite latitude/longitude pair or both absent. No geocoding or repair occurs. New records become public only when the dataset explicitly says `status: published` and `is_active: true`. Existing draft or review content remains a reported conflict.

Media is not imported in version 1. The frontend's approved curated media fallback remains authoritative until rights/provenance metadata can be represented completely in a reviewed dataset.

## Commands

Run from `backend`:

```text
python -m scripts.seed_destinations
python -m scripts.seed_destinations --dataset data/dev/destinations.json
```

Both commands are dry runs. After reviewing the plan and confirming a development environment, a human may intentionally apply it:

```text
python -m scripts.seed_destinations --apply
```

Do not use this importer as a production publication mechanism.

## Local PostgreSQL/PostGIS workflow on Windows

The repository's Docker Compose backend is the preferred execution environment. It mounts `backend/` at `/app` and receives the same `DATABASE_URL` used by the running API, so it avoids an accidental local SQLite fallback without duplicating or printing credentials.

From the repository root in PowerShell:

```text
docker compose up -d
docker compose ps
docker compose exec -T backend python -m scripts.check_database
docker compose exec -T backend python -m scripts.check_migrations
docker compose exec -T backend python -m alembic current
docker compose exec -T backend python -m alembic heads
docker compose exec -T backend python -m scripts.seed_destinations
```

The last command is dry-run because it omits `--apply`. A correct report identifies environment `development` and target `database / visitlibya`. A report identifying `local / ./visitlibya.db` means the command was launched outside the configured backend environment and must not be applied.

Compose requires local `POSTGRES_PASSWORD` and `DATABASE_URL` environment values, but commands and documentation must never echo them. The current development compose file mounts the backend source, so importer changes are immediately visible in the container. Rebuilding is necessary only when Python dependencies or the image definition change.

If the services are not already running, `docker compose up -d` starts them without resetting the named PostgreSQL volume. Do not run an Alembic upgrade as part of importer execution; compare `current` and `heads`, and stop for review if they differ.

## Idempotency and conflicts

The first conflict-free apply creates missing categories, destinations, and translation rows. A second run compares every managed field and reports the same rows as unchanged. A changed existing record is a conflict and receives no write; version 1 intentionally has no update mode.

## Verification after a human-approved apply

Check the public list, search, and each exact slug through the API. Only published, active rows should appear. Confirm Arabic and English translations and nullable coordinate serialization. The importer does not create trips or send anything to the Libya Tourist Atlas.

## Reviewed coordinate intake

`data/dev/destination-coordinates.reviewed.json` is an intentionally empty handoff envelope. Coordinate records may be added only from a supplied center-owned or otherwise approved local source. Each record requires an exact canonical destination slug, a complete validated pair, a source reference, and explicit `reviewed` status. Reviewer and review date remain null until truthful values are supplied.

Preview a handoff without changing any file or database:

```text
docker compose exec -T backend python -m scripts.merge_destination_coordinates
```

After an institutional source is supplied and reviewed, an authorized operator can explicitly update only the canonical JSON dataset:

```text
docker compose exec -T backend python -m scripts.merge_destination_coordinates --write-dataset
```

The write is atomic and reports before/after SHA-256 values. It never opens a database session. Unknown slugs and differences from an existing canonical coordinate pair block the write. Re-run the destination importer in dry-run mode after any dataset update; database apply remains a separate, human-approved action.
