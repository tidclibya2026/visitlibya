# Environment Variable Contract

Owners and sources remain approval placeholders. Examples are format markers, not active values. “Required” means explicitly supplied in that environment unless noted.

| Variable | Purpose | Staging | Production | Sensitivity | Accepted format and validation | Owner / source | Rotation | Consumer | Safe example format |
|---|---|---|---|---|---|---|---|---|---|
| `APP_ENV` | Policy mode | Required | Required | Non-sensitive | `staging` or `production` | `<OWNER>` / `<CONFIG_SOURCE>` | No | Settings | `<ENVIRONMENT_NAME>` |
| `DEBUG` | Debug behavior | Required, false preferred | Required, must be `false` | Non-sensitive | Boolean | `<OWNER>` / `<CONFIG_SOURCE>` | No | Settings | `<TRUE_OR_FALSE>` |
| `DATABASE_URL` | Psycopg connection | Required | Required | Sensitive | PostgreSQL SQLAlchemy URL; production rejects SQLite and loopback hosts | `<DB_OWNER>` / `<SECRET_MANAGER>` | On compromise/policy | SQLAlchemy | `<PRODUCTION_DATABASE_URL_FROM_SECRET_MANAGER>` |
| `JWT_SECRET_KEY` | Token signing | Required | Required | Sensitive | Non-empty; production minimum 48 characters, diverse, non-placeholder | `<SECURITY_OWNER>` / `<SECRET_MANAGER>` | Scheduled and incident-driven | Auth service | `<NEW_PRODUCTION_JWT_SECRET_FROM_SECRET_MANAGER>` |
| `CORS_ORIGINS` | Browser allowlist | Required | Required | Non-sensitive | Comma list/JSON list of exact HTTP(S) origins; no paths, queries, fragments, credentials, slash, wildcard | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On approved origin change | CORS middleware | `<APPROVED_HTTPS_FRONTEND_ORIGIN>` |
| `TRUSTED_HOSTS` | Host-header allowlist | Required | Required | Non-sensitive | Hostnames only; no schemes, paths, whitespace, credentials, wildcard | `<NETWORK_OWNER>` / `<CONFIG_SOURCE>` | On API host change | Trusted-host middleware | `<CONFIRMED_PRODUCTION_API_HOST>` |
| `FORWARDED_ALLOW_IPS` | Trusted proxy allowlist | Required | Required | Non-sensitive | IP/CIDR list; production wildcard prohibited | `<NETWORK_OWNER>` / `<CONFIG_SOURCE>` | On proxy topology change | Uvicorn | `<VERIFIED_PROXY_CIDR>` |
| `DATABASE_SSL_MODE` | DB TLS enforcement | Required | Required | Non-sensitive | `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`; production policy requires TLS | `<DB_OWNER>` / `<CONFIG_SOURCE>` | On trust-policy change | Psycopg | `<APPROVED_DATABASE_SSL_MODE>` |
| `DATABASE_CONNECT_TIMEOUT` | DB connection deadline | Optional | Required | Non-sensitive | Positive integer seconds | `<APP_OWNER>` / `<CONFIG_SOURCE>` | No | SQLAlchemy/Psycopg | `<POSITIVE_SECONDS>` |
| `DATABASE_POOL_SIZE` | Base pool per process | Optional | Required | Non-sensitive | Positive integer within approved connection budget | `<APP_DB_OWNER>` / `<CONFIG_SOURCE>` | On sizing change | SQLAlchemy | `<APPROVED_POOL_SIZE>` |
| `DATABASE_MAX_OVERFLOW` | Burst pool per process | Optional | Required | Non-sensitive | Non-negative integer within connection budget | `<APP_DB_OWNER>` / `<CONFIG_SOURCE>` | On sizing change | SQLAlchemy | `<APPROVED_MAX_OVERFLOW>` |
| `DATABASE_POOL_TIMEOUT` | Pool wait deadline | Optional | Required | Non-sensitive | Positive integer seconds | `<APP_DB_OWNER>` / `<CONFIG_SOURCE>` | On sizing change | SQLAlchemy | `<POSITIVE_SECONDS>` |
| `DATABASE_POOL_RECYCLE` | Connection recycle | Optional | Required | Non-sensitive | Positive integer seconds below infrastructure idle limit | `<APP_DB_OWNER>` / `<CONFIG_SOURCE>` | On policy change | SQLAlchemy | `<POSITIVE_SECONDS>` |
| `LOG_LEVEL` | Runtime verbosity | Optional | Required | Non-sensitive | `CRITICAL`, `ERROR`, `WARNING`, `INFO`, or `DEBUG`; production approval for `DEBUG` | `<OPS_OWNER>` / `<CONFIG_SOURCE>` | No | Logging | `<APPROVED_LOG_LEVEL>` |
| `ENABLE_DOCS` | Swagger UI exposure | Optional | Required | Non-sensitive | Boolean; normally false in production | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On approval change | FastAPI | `<TRUE_OR_FALSE>` |
| `ENABLE_REDOC` | ReDoc exposure | Optional | Required | Non-sensitive | Boolean; normally false in production | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On approval change | FastAPI | `<TRUE_OR_FALSE>` |
| `ENABLE_OPENAPI` | Schema exposure | Optional | Required | Non-sensitive | Boolean; normally false in production | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On approval change | FastAPI | `<TRUE_OR_FALSE>` |
| `PORT` | Container listen port | Required | Required | Non-sensitive | Integer 1024–65535; contract default 8000 | `<PLATFORM_OWNER>` / `<CONFIG_SOURCE>` | No | Uvicorn | `<CONTAINER_PORT>` |
| `WEB_CONCURRENCY` | Worker count | Required | Required | Non-sensitive | Integer 1–64; approved against CPU and DB budget | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On sizing change | Uvicorn | `<APPROVED_WORKER_COUNT>` |
| `API_PREFIX` | API route prefix | Optional | Required | Non-sensitive | Begins with one `/`, no trailing slash | `<APP_OWNER>` / `<CONFIG_SOURCE>` | On API version change | FastAPI | `<API_ROUTE_PREFIX>` |
| `JWT_ALGORITHM` | Token algorithm | Optional | Required | Non-sensitive | Current application contract: `HS256` | `<SECURITY_OWNER>` / `<CONFIG_SOURCE>` | On approved crypto migration | Auth service | `<APPROVED_JWT_ALGORITHM>` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | Optional | Required | Non-sensitive | Integer 5–1440 | `<SECURITY_OWNER>` / `<CONFIG_SOURCE>` | On security-policy change | Auth service | `<APPROVED_TOKEN_MINUTES>` |

