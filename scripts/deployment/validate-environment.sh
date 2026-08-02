#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import ipaddress
import os
import re
import sys
from urllib.parse import urlsplit

required = (
    "APP_ENV DEBUG DATABASE_URL JWT_SECRET_KEY CORS_ORIGINS TRUSTED_HOSTS "
    "FORWARDED_ALLOW_IPS DATABASE_SSL_MODE DATABASE_CONNECT_TIMEOUT DATABASE_POOL_SIZE "
    "DATABASE_MAX_OVERFLOW DATABASE_POOL_TIMEOUT DATABASE_POOL_RECYCLE LOG_LEVEL "
    "ENABLE_DOCS ENABLE_REDOC ENABLE_OPENAPI PORT WEB_CONCURRENCY API_PREFIX "
    "JWT_ALGORITHM ACCESS_TOKEN_EXPIRE_MINUTES"
).split()
errors = [f"{name} is required." for name in required if not os.environ.get(name, "").strip()]
app_env = os.environ.get("APP_ENV", "")
if app_env not in {"staging", "production"}:
    errors.append("APP_ENV must be staging or production.")
if app_env == "production" and os.environ.get("DEBUG", "").lower() != "false":
    errors.append("DEBUG must be false in production.")

db = os.environ.get("DATABASE_URL", "")
db_match = re.fullmatch(r"postgresql(?:\+psycopg)?://[^\s/@:]+(?::[^\s/@]*)?@(?P<host>\[[^\]]+\]|[^\s/:?#]+)(?::\d+)?/[^\s?#]+", db)
if db and not db_match:
    errors.append("DATABASE_URL must be a structurally valid PostgreSQL URL.")
elif db_match and app_env == "production" and db_match.group("host").strip("[]").lower() in {"localhost", "127.0.0.1", "::1"}:
    errors.append("Production DATABASE_URL must not use a loopback host.")
if app_env == "production" and db.lower().startswith("sqlite"):
    errors.append("SQLite is prohibited in production.")

jwt = os.environ.get("JWT_SECRET_KEY", "")
if jwt and (len(jwt) < 48 or len(set(jwt)) < 12 or re.search(r"placeholder|replace|example|change-me|test-only|[<>]", jwt, re.I)):
    errors.append("JWT_SECRET_KEY fails minimum structural quality.")

origins = [item for item in os.environ.get("CORS_ORIGINS", "").split(",") if item]
for origin in origins:
    try:
        parsed = urlsplit(origin)
        valid = (origin != "*" and not origin.endswith("/") and parsed.scheme in {"http", "https"}
                 and parsed.hostname and not parsed.username and not parsed.password and parsed.path == ""
                 and not parsed.query and not parsed.fragment)
    except ValueError:
        valid = False
    if not valid:
        errors.append("CORS_ORIGINS contains an invalid origin.")
if app_env == "production" and "https://tidclibya2026.github.io" not in origins:
    errors.append("Production CORS_ORIGINS must contain the confirmed exact frontend origin.")

host_pattern = re.compile(r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$")
for host in filter(None, os.environ.get("TRUSTED_HOSTS", "").split(",")):
    if host == "*" or not host_pattern.fullmatch(host):
        errors.append("TRUSTED_HOSTS contains invalid syntax.")
for proxy in filter(None, os.environ.get("FORWARDED_ALLOW_IPS", "").split(",")):
    if proxy == "*":
        errors.append("Wildcard proxy trust is prohibited.")
        continue
    try:
        ipaddress.ip_network(proxy, strict=False)
    except ValueError:
        errors.append("FORWARDED_ALLOW_IPS contains invalid IP/CIDR syntax.")

for name, low, high in (("PORT", 1024, 65535), ("WEB_CONCURRENCY", 1, 64)):
    try:
        valid = low <= int(os.environ.get(name, "")) <= high
    except ValueError:
        valid = False
    if not valid:
        errors.append(f"{name} must be an integer in the approved range.")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Environment validation failed with {len(errors)} error(s); values were not displayed.")
    raise SystemExit(1)
print("Environment validation passed; values were not displayed.")
PY

