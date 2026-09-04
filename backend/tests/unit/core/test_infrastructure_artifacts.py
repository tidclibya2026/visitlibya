import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
NEW_ROOTS = [ROOT / "deploy", ROOT / "docs" / "adr", ROOT / "docs" / "infrastructure", ROOT / "config" / "provider-evaluation.json"]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def artifact_files() -> list[Path]:
    files: list[Path] = []
    for item in NEW_ROOTS:
        files.extend(item.rglob("*") if item.is_dir() else [item])
    return [path for path in files if path.is_file()]


def test_adr_remains_proposed_and_no_provider_is_selected() -> None:
    adr = read("docs/adr/ADR-001-production-hosting-architecture.md")
    assert "Status: Proposed" in adr
    assert "Status: Accepted" not in adr
    data = json.loads(read("config/provider-evaluation.json"))
    assert data["status"] == "proposed"
    assert data["providers"] == []
    assert data["providerEntryTemplate"]["confidence"] == "unverified"
    assert data["providerEntryTemplate"]["scores"] == []


def test_weighted_provider_criteria_total_exactly_100() -> None:
    data = json.loads(read("config/provider-evaluation.json"))
    assert sum(item["weight"] for item in data["criteria"]) == 100
    assert data["scoringScale"] == {"minimum": 0, "maximum": 5}


def test_templates_contain_no_active_production_credentials_or_hostname() -> None:
    production = read("deploy/environment/production.env.example")
    staging = read("deploy/environment/staging.env.example")
    assert production != staging
    assert "DATABASE_URL=<PRODUCTION_DATABASE_URL_FROM_SECRET_MANAGER>" in production
    assert "JWT_SECRET_KEY=<NEW_PRODUCTION_JWT_SECRET_FROM_SECRET_MANAGER>" in production
    assert "TRUSTED_HOSTS=<CONFIRMED_PRODUCTION_API_HOST>" in production
    assert "DATABASE_URL=<STAGING_DATABASE_URL_FROM_SECRET_MANAGER>" in staging
    assert "JWT_SECRET_KEY=<NEW_STAGING_JWT_SECRET_FROM_SECRET_MANAGER>" in staging
    assert not re.search(r"DATABASE_URL=postgres(?:ql)?(?:\+\w+)?://", production + staging)
    assert not re.search(r"JWT_SECRET_KEY=(?!<)[^\r\n]+", production + staging)
    assert not re.search(r"TRUSTED_HOSTS=(?!<)[^\r\n]+", production + staging)


def test_frontend_stays_disabled_except_on_loopback() -> None:
    frontend = read("config/frontend-config.js")
    assert 'hostname === "localhost"' in frontend
    assert 'hostname === "127.0.0.1"' in frontend
    assert 'isLocal ? "http://127.0.0.1:8001/api/v1" : ""' in frontend
    assert "apiEnabled: isLocal" in frontend
    assert 'deploymentEnvironment: isLocal ? "local" : "static"' in frontend


def test_cors_documentation_uses_exact_confirmed_origin() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in artifact_files() if path.suffix in {".md", ".example"})
    assert "https://tidclibya2026.github.io" in text
    assert "https://tidclibya2026.github.io/visitlibya/" not in text
    production = read("deploy/environment/production.env.example")
    assert "CORS_ORIGINS=*" not in production
    assert "TRUSTED_HOSTS=*" not in production
    assert "FORWARDED_ALLOW_IPS=*" not in production


def test_sql_role_template_is_safe_and_non_destructive() -> None:
    sql = read("deploy/database/roles.example.sql")
    upper = sql.upper()
    assert not re.search(r"\bPASSWORD\s+['\"]", upper)
    assert not re.search(r"\bDROP\b", upper)
    app_line = next(line.upper() for line in sql.splitlines() if line.startswith("CREATE ROLE") and "APPLICATION_ROLE" in line)
    assert " NOSUPERUSER" in app_line and " NOCREATEDB" in app_line and " NOCREATEROLE" in app_line
    assert not re.search(r"(?<!NO)SUPERUSER", app_line)
    assert not re.search(r"(?<!NO)CREATEDB", app_line)
    assert not re.search(r"(?<!NO)CREATEROLE", app_line)


def test_database_is_private_and_migrations_are_separate() -> None:
    specification = read("docs/infrastructure/production-infrastructure-specification.md").lower()
    runtime = read("deploy/container-runtime-contract.md").lower()
    compose = read("docker-compose.production.example.yml")
    assert "publicly exposed database port" in specification
    assert "never run migrations during web startup" in runtime
    assert "alembic" not in next(line.lower() for line in read("backend/Dockerfile").splitlines() if line.startswith("CMD"))
    assert not re.search(r"postgres:[^\n]*ports:|ports:[\s\S]{0,100}-\s*[\"']?5432:5432", compose)


def test_release_gates_and_runbooks_cover_required_controls() -> None:
    gates = read("docs/infrastructure/production-release-gates.md").lower()
    for term in ("backup", "restore", "security approval", "legal/privacy", "monitoring", "rollback"):
        assert term in gates
    for name in ("staging-deployment.md", "production-deployment.md", "rollback.md", "incident-response.md"):
        assert (ROOT / "deploy" / "runbooks" / name).is_file()


def test_no_provider_manifests_cloud_credentials_or_private_keys() -> None:
    forbidden_names = {"main.tf", "terraform.tf", "render.yaml", "railway.json", "fly.toml", "app.yaml", "Chart.yaml"}
    assert not any(path.name in forbidden_names or path.suffix in {".tf", ".tfvars"} for path in artifact_files())
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in artifact_files())
    assert "BEGIN PRIVATE KEY" not in text
    assert "AWS_SECRET_ACCESS_KEY=" not in text
    assert "AZURE_CLIENT_SECRET=" not in text
    assert "GOOGLE_APPLICATION_CREDENTIALS=" not in text


def test_backend_workflow_uses_module_pytest_invocation() -> None:
    workflow = read(".github/workflows/backend-production-validation.yml")
    assert "python -m pytest -q tests/unit/core/test_config.py tests/unit/core/test_production_artifacts.py" in workflow
    assert "run: python -m pytest -q" in workflow
    assert not re.search(r"(?m)^\s+(?:run:\s*)?pytest\s+-q", workflow)


def test_preflight_branch_override_preserves_strict_fallback_and_other_checks() -> None:
    bash = read("scripts/deployment/preflight.sh")
    powershell = read("scripts/deployment/preflight.ps1")
    workflow = read(".github/workflows/infrastructure-artifact-validation.yml")

    assert 'branch="${PREFLIGHT_GIT_BRANCH:-$(git -C "$root" branch --show-current 2>/dev/null || true)}"' in bash
    assert "[[ -n \"$branch\" ]] || fail 'Git branch could not be determined.'" in bash
    assert "$env:PREFLIGHT_GIT_BRANCH" in powershell
    assert "git -C $root branch --show-current" in powershell
    assert "if ([string]::IsNullOrWhiteSpace($branch)) { Fail 'Git branch could not be determined.' }" in powershell
    assert "if (-not $?) { Fail 'Environment validation failed.' }" in powershell
    assert "if ($LASTEXITCODE -ne 0) { Fail 'Environment validation failed.' }" not in powershell
    assert "PREFLIGHT_GIT_BRANCH: ${{ github.head_ref || github.ref_name }}" in workflow

    for script in (bash, powershell):
        assert "ALLOW_DIRTY_GIT" in script
        assert "IMAGE_REFERENCE" in script
        assert "Environment validation failed." in script

