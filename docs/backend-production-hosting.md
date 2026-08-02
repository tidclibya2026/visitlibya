# Backend production hosting

## Architecture

Use a managed HTTPS container service with managed PostgreSQL/PostGIS when available. A VPS container host with managed PostgreSQL/PostGIS is the second choice. A single Docker Compose VPS is a continuity fallback with materially higher patching, backup, TLS, and monitoring burden. Kubernetes is not part of this repository and is not recommended at the current scale.

Traffic flows from the static GitHub Pages frontend to a managed TLS proxy, then to Uvicorn/FastAPI, services, repositories, SQLAlchemy, and PostgreSQL/PostGIS. TLS terminates outside the container unless a later provider decision states otherwise.

## Required production configuration

`APP_ENV=production`, `DEBUG=false`, `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, and `TRUSTED_HOSTS` are mandatory. Also configure `FORWARDED_ALLOW_IPS`, database pool/connect/SSL values, token expiry, log level, and documentation controls. Use a platform secret store; never bake these values into an image or repository file.

Production rejects loopback databases, wildcard CORS/trusted/proxy allowlists, weak signing secrets, path-bearing origins, and enabled debug. Swagger, ReDoc, and OpenAPI default off.

## Proxy and TLS

The container enables Uvicorn proxy-header parsing but trusts only `FORWARDED_ALLOW_IPS`. Set that value to the confirmed proxy address/network. Do not use `*`. Configure the final API hostname in `TRUSTED_HOSTS`. HTTPS redirects and HSTS are deferred until TLS termination and proxy behavior are confirmed, preventing redirect loops and false security signaling.

## Staging

Use `APP_ENV=staging`, separate secrets/database, explicit staging hosts/origins, and the same migration and validation order as production. Never share production credentials or data by default.

## Provider decisions still required

- hosting provider, region/data-residency approval, API hostname, and TLS owner;
- database service/PostGIS enablement and connection limits;
- monitoring/error provider and alert routing;
- approved backup retention, RPO, RTO, incident contacts, and legal/security review.
