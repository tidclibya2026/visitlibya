# Database Provisioning Checklist

- [ ] PostgreSQL 16 compatibility verified from authoritative evidence.
- [ ] PostGIS 3.4 compatibility and required extension privileges verified.
- [ ] Psycopg 3 connection compatibility tested in isolated staging.
- [ ] Private endpoint configured; a public database port is prohibited.
- [ ] TLS required; prefer `verify-full` where supported and document exceptions.
- [ ] CA bundle ownership, distribution, rotation, and expiry monitoring assigned.
- [ ] Database encoding is UTF-8.
- [ ] Arabic/English collation and search behavior decision approved and tested.
- [ ] UTC database/application timezone decision approved.
- [ ] Initial storage sizing, performance class, and growth forecast approved.
- [ ] Storage auto-growth limit and exhaustion alert approved.
- [ ] Connection limit recorded.
- [ ] Application pool calculation includes replicas × workers × (pool + overflow), migrations, operations, and reserve.
- [ ] Statement timeout decision recorded.
- [ ] Lock timeout decision recorded.
- [ ] Maintenance window and notification ownership approved.
- [ ] Automated backup schedule and retention approved.
- [ ] PITR window and transaction-log health monitoring approved.
- [ ] Isolated restore test completed with integrity evidence.
- [ ] Database, PostGIS, connection, storage, replication, backup, and PITR monitoring configured.
- [ ] Separate migration role provisioned with only approved schema privileges.
- [ ] Separate application role provisioned without ownership or role/database creation.
- [ ] Separate backup/restore role approved with bounded capabilities.
- [ ] Export/exit test completed and recovery documentation retained outside the service.

