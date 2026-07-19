from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CategoryCodeConflictError,
    CategoryError,
    CategoryIntegrityError,
    CategoryNotFoundError,
    CategoryPersistenceError,
)
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(
        self,
        session: Session,
        repository: CategoryRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or CategoryRepository(session)

    def list_categories(
        self,
        *,
        skip: int,
        limit: int,
        is_active: bool | None,
    ) -> tuple[Sequence[Category], int]:
        try:
            total = self.repository.count(is_active=is_active)
            items = self.repository.list(
                skip=skip,
                limit=limit,
                is_active=is_active,
            )
            return items, total
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise CategoryPersistenceError() from exc

    def get_category_by_code(self, code: str) -> Category:
        try:
            category = self.repository.get_by_code(code.strip().lower())
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise CategoryPersistenceError() from exc
        if category is None:
            raise CategoryNotFoundError()
        return category

    def get_category_by_id(self, category_id: int) -> Category:
        try:
            category = self.repository.get_by_id(category_id)
        except SQLAlchemyError as exc:
            self._rollback_failed_read()
            raise CategoryPersistenceError() from exc
        if category is None:
            raise CategoryNotFoundError()
        return category

    def create_category(self, payload: CategoryCreate) -> Category:
        try:
            code = payload.code.strip().lower()
            self._ensure_code_available(code)
            values = payload.model_dump()
            values["code"] = code
            category = Category(**values)
            self.repository.add(category)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(category)
            return category
        except CategoryError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise CategoryIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise CategoryPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def update_category(
        self,
        category_id: int,
        payload: CategoryUpdate,
    ) -> Category:
        try:
            category = self._get_required_category(category_id)
            values = payload.model_dump(exclude_unset=True)
            new_code = values.get("code")
            if new_code is not None:
                normalized_code = new_code.strip().lower()
                self._ensure_code_available(
                    normalized_code,
                    exclude_category_id=category_id,
                )
                values["code"] = normalized_code
            for field, value in values.items():
                setattr(category, field, value)
            self.repository.flush()
            self.session.commit()
            self.repository.refresh(category)
            return category
        except CategoryError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise CategoryIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise CategoryPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def delete_category(self, category_id: int) -> None:
        try:
            category = self._get_required_category(category_id)
            self.repository.delete(category)
            self.repository.flush()
            self.session.commit()
        except CategoryError:
            self.session.rollback()
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise CategoryIntegrityError() from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise CategoryPersistenceError() from exc
        except Exception:
            self.session.rollback()
            raise

    def _ensure_code_available(
        self,
        code: str,
        exclude_category_id: int | None = None,
    ) -> None:
        if self.repository.code_exists(code, exclude_category_id):
            raise CategoryCodeConflictError()

    def _get_required_category(self, category_id: int) -> Category:
        category = self.repository.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError()
        return category

    def _rollback_failed_read(self) -> None:
        if not self.session.is_active:
            self.session.rollback()
