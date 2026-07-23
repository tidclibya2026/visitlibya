from unittest.mock import MagicMock

from app.models.category import Category
from app.repositories.category import CategoryRepository


def test_get_by_id_and_code() -> None:
    category = Category(id=1, code="heritage", name_ar="تراث", name_en="Heritage")
    session = MagicMock()
    session.scalar.side_effect = [category, category]
    repository = CategoryRepository(session)

    assert repository.get_by_id(1) is category
    assert repository.get_by_code("heritage") is category
    assert session.scalar.call_count == 2


def test_code_exists_supports_excluding_category() -> None:
    session = MagicMock()
    session.scalar.side_effect = [1, None]
    repository = CategoryRepository(session)

    assert repository.code_exists("heritage") is True
    assert repository.code_exists("heritage", exclude_category_id=1) is False


def test_list_and_count_apply_active_filter() -> None:
    category = Category(id=1, code="heritage", name_ar="تراث", name_en="Heritage")
    scalar_result = MagicMock()
    scalar_result.all.return_value = [category]
    session = MagicMock()
    session.scalars.return_value = scalar_result
    session.scalar.return_value = 1
    repository = CategoryRepository(session)

    items = repository.list(skip=0, limit=20, is_active=True)
    total = repository.count(is_active=True)

    assert list(items) == [category]
    assert total == 1
    assert "is_active" in str(session.scalars.call_args.args[0])
    assert "is_active" in str(session.scalar.call_args.args[0])


def test_write_helpers_do_not_manage_transactions() -> None:
    category = Category(code="heritage", name_ar="تراث", name_en="Heritage")
    session = MagicMock()
    repository = CategoryRepository(session)

    repository.add(category)
    repository.flush()
    repository.refresh(category)
    repository.delete(category)

    session.add.assert_called_once_with(category)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(category)
    session.delete.assert_called_once_with(category)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
