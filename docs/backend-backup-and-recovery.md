# Backend backup and recovery

No operational commitments are selected by this repository. Before production, owners must approve:

- backup owner and platform;
- encryption/key ownership;
- full backup frequency and retention: **TBD**;
- point-in-time recovery availability/window: **TBD**;
- RPO: **TBD**;
- RTO: **TBD**;
- restore-test frequency and evidence retention: **TBD**;
- media-object backup policy, if API media storage is introduced;
- incident, failover, and legal notification contacts: **TBD**.

Backups must preserve PostgreSQL/PostGIS extension and spatial objects. Use provider-native snapshots/PITR or version-compatible `pg_dump`/`pg_restore` procedures, encrypt in transit and at rest, restrict restore access, and keep credentials outside backup scripts.

Test restore into an isolated non-production database: restore, confirm PostGIS, compare Alembic head, run controlled integrity checks, and record duration/results without personal data or credentials. Never test by overwriting production. Take and verify a backup before destructive migrations.
