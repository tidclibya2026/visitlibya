import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE = {"_env_file": None, "database_url": "sqlite:///:memory:", "jwt_secret_key": "x" * 32}


def test_approval_mutations_default_disabled():
    settings = Settings(**BASE)
    assert not settings.publication_governance_enabled
    assert not settings.publication_approval_mutations_enabled
    assert settings.publication_decision_storage == "unconfigured"


def test_placeholder_or_incomplete_configuration_cannot_enable_mutations():
    with pytest.raises(ValidationError):
        Settings(**BASE, publication_approval_mutations_enabled=True)


def test_production_rejects_approval_mutation_even_with_claimed_configuration():
    with pytest.raises(ValidationError):
        Settings(**BASE, app_env="production", publication_governance_enabled=True,
                 publication_approval_mutations_enabled=True)
