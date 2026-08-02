# Database and Application Role Model

| Identity | Allowed privileges | Prohibited privileges | Credential source | Rotation | Audit | Approval owner |
|---|---|---|---|---|---|---|
| Infrastructure administrator | Provision/configure approved database service and network; emergency administration | Routine application use; shared credentials | Approved privileged identity system | Policy and incident driven | All administrative actions | `<INFRASTRUCTURE_OWNER>` |
| Deployment operator | Run approved release job and read release health evidence | Direct content changes; unrestricted DB administration | Approved deployment identity | Policy and incident driven | Release and configuration events | `<RELEASE_OWNER>` |
| Migration DB identity | Connect; use target schema; create/alter application schema objects required by reviewed migrations | Superuser, role creation, database creation, unrelated schemas | Secret manager/workload identity | Scheduled and incident driven | Connections and DDL | `<DB_OWNER>` |
| Application DB identity | Connect; schema usage; bounded DML and sequence use required by API | Superuser, create database/role, schema ownership, arbitrary DDL | Secret manager/workload identity | Scheduled and incident driven | Connections and anomalous DML | `<APP_DB_OWNER>` |
| Backup/restore identity | Approved backup/export and controlled isolated restore operations | Application traffic; role administration beyond restore need | Privileged secret/identity system | Policy and incident driven | Every backup/restore/export | `<RECOVERY_OWNER>` |
| Application content administrator | Authorized API-level content management | Direct DB login; infrastructure or identity administration | Application identity provider | Policy and incident driven | Administrative API actions | `<CONTENT_OWNER>` |
| Optional read-only analyst | Approved views/read-only queries with privacy controls | DML, DDL, raw sensitive fields, role/database creation | Approved analytics identity | Scheduled and incident driven | Queries and exports | `<DATA_OWNER>` |

