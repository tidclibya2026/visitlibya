import pytest

from scripts import validate_libya_boundary_postgis as validator


def valid_row():
    return {
        **validator.EXPECTED_VALUES,
        "geometry_points": 100,
        "min_x": 9.0,
        "min_y": 19.0,
        "max_x": 25.0,
        "max_y": 34.0,
        "area_km2": 1_700_000.0,
    }


class Mappings:
    def __init__(self, rows): self.rows = rows
    def mappings(self): return self
    def all(self): return self.rows


class FakeSession:
    def __init__(self, rows): self.rows = rows
    def execute(self, _statement): return Mappings(self.rows)
    def close(self): pass


@pytest.mark.parametrize("rows", [[], [valid_row(), valid_row()]])
def test_validator_requires_exactly_one_ly_row(rows):
    with pytest.raises(validator.BoundaryValidationError, match="exactly one"):
        validator.validate_database(lambda: FakeSession(rows))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("is_validated", False),
        ("is_published", True),
        ("geometry_srid", 3857),
        ("geometry_is_valid", False),
        ("source_geometry_sha256", "0" * 64),
        ("geometry_type", "POLYGON"),
    ],
)
def test_validator_rejects_governance_failure(field, value):
    row = valid_row()
    row[field] = value
    with pytest.raises(validator.BoundaryValidationError, match=field):
        validator.validate_row(row)


def test_validator_accepts_validated_unpublished_multipolygon():
    row = valid_row()
    assert validator.validate_database(lambda: FakeSession([row])) == row
