class DestinationError(Exception):
    """Base class for destination domain errors."""


class DestinationNotFoundError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination not found")


class DestinationSlugConflictError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Destination slug already exists")


class CategoryNotFoundError(DestinationError):
    def __init__(self) -> None:
        super().__init__("Category not found")


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
