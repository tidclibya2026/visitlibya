from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.sql.elements import ColumnElement

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):

    @staticmethod
    def _build_filters(*, is_active: bool | None) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if is_active is not None:
            filters.append(Category.is_active == is_active)
        return filters

    def get_by_id(self, category_id: int) -> Category | None:
        return self.session.scalar(
            select(Category).where(Category.id == category_id)
        )

    def get_by_code(self, code: str) -> Category | None:
        return self.session.scalar(select(Category).where(Category.code == code))

    def code_exists(
        self,
        code: str,
        exclude_category_id: int | None = None,
    ) -> bool:
        statement = select(Category.id).where(Category.code == code)
        if exclude_category_id is not None:
            statement = statement.where(Category.id != exclude_category_id)
        return self.session.scalar(statement.limit(1)) is not None

    def list(
        self,
        *,
        skip: int,
        limit: int,
        is_active: bool | None,
    ) -> Sequence[Category]:
        filters = self._build_filters(is_active=is_active)
        statement = (
            select(Category)
            .where(*filters)
            .order_by(Category.id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def count(self, *, is_active: bool | None) -> int:
        filters = self._build_filters(is_active=is_active)
        statement: Select[tuple[int]] = select(func.count(Category.id)).where(
            *filters
        )
        return self.session.scalar(statement) or 0
