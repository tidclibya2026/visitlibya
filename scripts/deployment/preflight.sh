#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
errors=0
fail() { printf '%s\n' "$1" >&2; errors=$((errors + 1)); }

for tool in git node python3; do command -v "$tool" >/dev/null 2>&1 || fail "Required tool is unavailable: $tool"; done
branch="$(git -C "$root" branch --show-current 2>/dev/null || true)"
[[ -n "$branch" ]] || fail 'Git branch could not be determined.'
if [[ "${ALLOW_DIRTY_GIT:-}" != 'true' ]] && [[ -n "$(git -C "$root" status --porcelain)" ]]; then fail 'Git state is not clean or explicitly approved.'; fi
if [[ ! "${IMAGE_REFERENCE:-}" =~ ^[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9._-]+|@sha256:[a-f0-9]{64})$ ]]; then fail 'IMAGE_REFERENCE format is invalid.'; fi

bash "$root/scripts/deployment/validate-environment.sh" || fail 'Environment validation failed.'
for file in \
  docs/adr/ADR-001-production-hosting-architecture.md \
  docs/infrastructure/production-infrastructure-specification.md \
  docs/infrastructure/production-release-gates.md \
  deploy/health/health-check-contract.md \
  backend/scripts/check_migrations.py; do
  [[ -f "$root/$file" ]] || fail "Required artifact is missing: $file"
done
grep -Eq 'apiEnabled:[[:space:]]*false' "$root/config/frontend-config.js" || fail 'Frontend apiEnabled is not false.'
grep -Eq 'apiBaseUrl:[[:space:]]*""' "$root/config/frontend-config.js" || fail 'Frontend apiBaseUrl is not empty.'
grep -Eq 'deploymentEnvironment:[[:space:]]*"static"' "$root/config/frontend-config.js" || fail 'Frontend environment is not static.'

if (( errors > 0 )); then printf '%s\n' 'Preflight failed; no deployment was performed.'; exit 1; fi
printf '%s\n' 'Preflight passed; no deployment, database connection, image push, or cloud action was performed.'

