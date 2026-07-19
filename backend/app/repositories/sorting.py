from collections.abc import Mapping
from typing import Literal

from sqlalchemy import asc, desc
from sqlalchemy.sql.elements import ColumnElement


SortOrder = Literal["asc", "desc"]


def safe_order_by(
    sort_by: str,
    sort_order: SortOrder,
    allowed_columns: Mapping[str, ColumnElement[object]],
) -> ColumnElement[object]:
    column = allowed_columns[sort_by]
    return desc(column) if sort_order == "desc" else asc(column)
