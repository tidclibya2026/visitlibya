from sqlalchemy import CheckConstraint

from app.models.review import Review


def test_review_schema_constraints_and_foreign_keys() -> None:
    table = Review.__table__
    checks = [constraint for constraint in table.constraints if isinstance(constraint, CheckConstraint)]
    assert table.name == "reviews"
    assert any("rating >= 1" in str(constraint.sqltext) for constraint in checks)
    destination_fk = next(iter(table.c.destination_id.foreign_keys))
    user_fk = next(iter(table.c.user_id.foreign_keys))
    assert destination_fk.target_fullname == "destinations.id" and destination_fk.ondelete == "CASCADE"
    assert user_fk.target_fullname == "users.id" and user_fk.ondelete == "SET NULL"
