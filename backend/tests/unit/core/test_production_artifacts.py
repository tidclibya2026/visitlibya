from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]


def test_environment_examples_are_placeholder_only() -> None:
    for relative in ("backend/.env.example", "backend/.env.production.example"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "postgresql://" not in content and "postgresql+psycopg://" not in content
        assert not re.search(r"(?im)^JWT_SECRET_KEY=(?!<)", content)
        assert not re.search(r"(?im)^DATABASE_URL=(?!<)", content)
        assert "tidclibya2026.github.io/visitlibya" not in content


def test_production_dockerfile_is_hardened() -> None:
    content = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    assert "USER visitlibya" in content
    assert "--reload" not in content
    assert "--proxy-headers" in content
    assert "COPY ." not in content
    assert "gcc" not in content and "libpq-dev" not in content


def test_frontend_runtime_remains_inactive() -> None:
    content = (ROOT / "config/frontend-config.js").read_text(encoding="utf-8")
    assert "apiEnabled: false" in content
    assert 'apiBaseUrl: ""' in content
    assert 'deploymentEnvironment: "static"' in content


def test_sensitive_operator_file_is_ignored() -> None:
    assert "backend/.envpython" in (ROOT / ".gitignore").read_text(encoding="utf-8")
