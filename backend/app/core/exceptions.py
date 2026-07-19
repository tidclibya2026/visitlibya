class DestinationError(Exception):
    """Base class for destination domain errors."""


class CategoryError(Exception):
    """Base class for category domain errors."""


class DestinationNotFoundError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination not found")


class DestinationSlugConflictError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination slug already exists")


class CategoryNotFoundError(DestinationError, CategoryError):
    def __init__(self) -> None:
        super().__init__("Category not found")


class CategoryCodeConflictError(CategoryError):
    def __init__(self) -> None:
        super().__init__("Category code already exists")


class CategoryIntegrityError(CategoryError):
    def __init__(self) -> None:
        super().__init__("Category conflicts with existing data")


class CategoryPersistenceError(CategoryError):
    def __init__(self) -> None:
        super().__init__("Category could not be persisted")


class DestinationTranslationConflictError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Each translation language_code must be unique")


class DestinationCoordinatesError(DestinationError):
    def __init__(self) -> None:
        super().__init__("latitude and longitude must be provided together")


class DestinationIntegrityError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination conflicts with existing data")


class DestinationPersistenceError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination could not be persisted")


class MediaError(Exception):
    """Base class for media domain errors."""


class MediaAssetNotFoundError(MediaError):
    def __init__(self) -> None:
        super().__init__("Media asset not found")


class MediaAssetPathConflictError(MediaError):
    def __init__(self) -> None:
        super().__init__("Media file path already exists")


class MediaAssetIntegrityError(MediaError):
    def __init__(self) -> None:
        super().__init__("Media asset conflicts with existing data")


class MediaAssetPersistenceError(MediaError):
    def __init__(self) -> None:
        super().__init__("Media request could not be persisted")


class DestinationMediaNotFoundError(MediaError):
    def __init__(self) -> None:
        super().__init__("Destination media association not found")


class DestinationMediaConflictError(MediaError):
    def __init__(self) -> None:
        super().__init__("Destination media association already exists")
