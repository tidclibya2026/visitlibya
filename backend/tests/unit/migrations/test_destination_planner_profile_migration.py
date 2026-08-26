from pathlib import Path


MIGRATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "16af7df9200c_add_destination_planner_profiles.py"
)


def test_destination_planner_profile_migration_exists():
    assert MIGRATION_PATH.exists()


def test_destination_planner_profile_migration_chain():
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "16af7df9200c"' in text
    assert (
        'down_revision: str | Sequence[str] | None = '
        '"a4902527f045"'
        in text
    )


def test_destination_planner_profile_table_contract():
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    assert '"destination_planner_profiles"' in text
    assert '"destination_id"' in text
    assert '"recommended_visit_minutes"' in text
    assert '"minimum_visit_minutes"' in text
    assert '"maximum_visit_minutes"' in text
    assert '"opening_hours"' in text
    assert '"access_status"' in text
    assert '"road_access"' in text
    assert '"road_surface"' in text
    assert '"road_condition"' in text
    assert '"planner_priority"' in text
    assert '"meal_suitability"' in text
    assert '"rest_suitability"' in text
    assert '"verification_status"' in text


def test_destination_planner_profile_one_to_one_contract():
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    assert '"uq_destination_planner_profile_destination"' in text
    assert '["destinations.id"]' in text
    assert 'ondelete="CASCADE"' in text


def test_destination_planner_profile_constraints_present():
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    required_constraints = [
        "destination_planner_recommended_visit_positive",
        "destination_planner_minimum_visit_positive",
        "destination_planner_maximum_visit_positive",
        "destination_planner_minimum_not_above_recommended",
        "destination_planner_maximum_not_below_recommended",
        "destination_planner_visit_range_valid",
        "destination_planner_priority_range",
        "destination_planner_meal_suitability_range",
        "destination_planner_rest_suitability_range",
    ]

    for constraint in required_constraints:
        assert constraint in text


def test_destination_planner_profile_downgrade_contract():
    text = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "op.drop_index(" in text
    assert (
        '"ix_destination_planner_profiles_destination_id"'
        in text
    )
    assert 'op.drop_table("destination_planner_profiles")' in text
