import pytest

from app.gis.layer_registry import LAYER_REGISTRY, get_layer, require_layer


EXPECTED_LAYERS = {
    "LIBYA_BOUNDARY", "WORLD_HERITAGE", "OLD_TRIPOLI", "NATURAL_SITES",
    "ARCHAEOLOGICAL_SITES", "HISTORICAL_SITES", "ROCK_ART",
}


def test_initial_governed_layer_registry_is_complete_and_unpublished():
    assert EXPECTED_LAYERS <= LAYER_REGISTRY.keys()
    assert all(layer.default_is_published is False for layer in LAYER_REGISTRY.values())
    assert all(layer.allowed_geometry_types for layer in LAYER_REGISTRY.values())


def test_registry_normalizes_layer_code():
    assert get_layer("world-heritage").layer_code == "WORLD_HERITAGE"


def test_invalid_layer_code_fails_closed():
    with pytest.raises(ValueError, match="Unknown governed GIS layer"):
        require_layer("unregistered")


def test_national_boundary_remains_specialized():
    assert require_layer("LIBYA_BOUNDARY").specialized_authority is True


def test_layer_geometry_policy_is_specific():
    world_heritage = require_layer("WORLD_HERITAGE")
    assert "POINT" in world_heritage.allowed_geometry_types
    assert "POLYGON" in world_heritage.allowed_geometry_types
    assert "LINESTRING" not in world_heritage.allowed_geometry_types
