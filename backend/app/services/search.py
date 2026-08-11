from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import SearchPersistenceError, SearchValidationError
from app.models.destination import DestinationTranslation
from app.repositories.search import SearchRepository, SearchResultRow
from app.schemas.search import (
    SearchCategoryItem,
    SearchDestinationItem,
    SearchDestinationResponse,
    SearchFilters,
    SearchSortField,
    SearchSortOrder,
)


class SearchService:
    def __init__(self, session: Session, repository: SearchRepository | None = None) -> None:
        self.session = session
        self.repository = repository or SearchRepository(session)

    def search_destinations(
        self,
        *,
        filters: SearchFilters,
        page: int,
        page_size: int,
        sort_by: SearchSortField,
        sort_order: SearchSortOrder,
    ) -> SearchDestinationResponse:
        self._validate_parameters(filters, page, page_size, sort_by, sort_order)
        try:
            rows, total = self.repository.search(
                filters=filters,
                offset=(page - 1) * page_size,
                limit=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        except SQLAlchemyError as exc:
            if not self.session.is_active:
                self.session.rollback()
            raise SearchPersistenceError() from exc
        return SearchDestinationResponse.create(
            items=[self._to_item(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _validate_parameters(
        filters: SearchFilters,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> None:
        if page < 1:
            raise SearchValidationError("page must be at least 1")
        if not 1 <= page_size <= 100:
            raise SearchValidationError("page_size must be between 1 and 100")
        if sort_by not in {
            "name",
            "created_at",
            "updated_at",
            "average_rating",
            "reviews_count",
        }:
            raise SearchValidationError("Unsupported search sort field")
        if sort_order not in {"asc", "desc"}:
            raise SearchValidationError("sort_order must be asc or desc")
        for value in (filters.minimum_rating, filters.maximum_rating):
            if value is not None and not 1 <= value <= 5:
                raise SearchValidationError(
                    "ratings must be between 1 and 5"
                )
        if (
            filters.minimum_rating is not None
            and filters.maximum_rating is not None
            and filters.minimum_rating > filters.maximum_rating
        ):
            raise SearchValidationError(
                "minimum_rating cannot exceed maximum_rating"
            )

    @classmethod
    def _to_item(cls, row: SearchResultRow) -> SearchDestinationItem:
        destination = row.destination
        translations = {
            translation.language_code.lower(): translation
            for translation in destination.translations
        }
        arabic = translations.get("ar")
        english = translations.get("en")
        category = destination.category
        return SearchDestinationItem(
            id=destination.id,
            slug=destination.slug,
            name_ar=cls._value(arabic, "name"),
            name_en=cls._value(english, "name"),
            short_description_ar=cls._value(arabic, "short_description"),
            short_description_en=cls._value(english, "short_description"),
            municipality=destination.municipality,
            region=destination.region,
            latitude=destination.latitude,
            longitude=destination.longitude,
            category=(
                SearchCategoryItem(
                    id=category.id,
                    code=category.code,
                    name_ar=category.name_ar,
                    name_en=category.name_en,
                )
                if category is not None
                else None
            ),
            primary_media_url=row.primary_media_url,
            is_featured=destination.is_featured,
            average_rating=row.average_rating,
            reviews_count=row.reviews_count,
        )

    @staticmethod
    def _value(
        translation: DestinationTranslation | None,
        attribute: str,
    ) -> str | None:
        return getattr(translation, attribute) if translation is not None else None
