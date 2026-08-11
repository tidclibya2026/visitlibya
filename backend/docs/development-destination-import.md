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

## Idempotency and conflicts

The first conflict-free apply creates missing categories, destinations, and translation rows. A second run compares every managed field and reports the same rows as unchanged. A changed existing record is a conflict and receives no write; version 1 intentionally has no update mode.

## Verification after a human-approved apply

Check the public list, search, and each exact slug through the API. Only published, active rows should appear. Confirm Arabic and English translations and nullable coordinate serialization. The importer does not create trips or send anything to the Libya Tourist Atlas.
