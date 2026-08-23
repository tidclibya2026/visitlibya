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


class DestinationPublicationBlockedError(DestinationError):
    def __init__(self) -> None:
        super().__init__("PUBLICATION_ELIGIBILITY_REQUIRED")


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


class ReviewError(Exception):
    """Base class for review domain errors."""


class ReviewNotFoundError(ReviewError):
    def __init__(self) -> None:
        super().__init__("Review not found")


class ReviewRatingError(ReviewError):
    def __init__(self) -> None:
        super().__init__("Review rating must be between 1 and 5")


class ReviewIntegrityError(ReviewError):
    def __init__(self) -> None:
        super().__init__("Review conflicts with existing data")


class ReviewPersistenceError(ReviewError):
    def __init__(self) -> None:
        super().__init__("Review could not be persisted")


class SearchError(Exception):
    """Base class for public destination search errors."""


class SearchValidationError(SearchError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchPersistenceError(SearchError):
    def __init__(self) -> None:
        super().__init__("Destination search could not be completed")


class AuthenticationError(Exception):
    """Base class for authentication domain errors."""


class InvalidCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Invalid username or password")


class InvalidTokenError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Could not validate credentials")


class InactiveUserError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Inactive user")


class AuthenticationPersistenceError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Authentication service is unavailable")


class RegistrationConflictError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("An account with this email or username already exists")


class EmailAlreadyRegisteredError(RegistrationConflictError):
    def __init__(self) -> None:
        AuthenticationError.__init__(
            self,
            "An account already exists with this email address",
        )


class UsernameAlreadyRegisteredError(RegistrationConflictError):
    def __init__(self) -> None:
        AuthenticationError.__init__(self, "This username is already in use")


class FavoriteError(Exception):
    """Base class for favorite domain errors."""


class FavoriteIntegrityError(FavoriteError):
    def __init__(self) -> None:
        super().__init__("Favorite conflicts with existing data")


class FavoritePersistenceError(FavoriteError):
    def __init__(self) -> None:
        super().__init__("Favorite request could not be completed")


class TripError(Exception):
    """Base class for trip-planner domain errors."""


class TripNotFoundError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip not found")


class TripItemNotFoundError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip item not found")


class InvalidTripDateRangeError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip end date must not be before its start date")


class InvalidTripDayError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip day is outside the trip date range")


class TripItemDateOutOfRangeError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip item visit date is outside the trip date range")


class DestinationUnavailableForTripError(TripError):
    def __init__(self) -> None:
        super().__init__("Destination is unavailable for trip planning")


class InvalidTripItemOrderError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip item order is invalid")


class TripItemLimitExceededError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip item limit has been reached")


class TripConcurrentModificationError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip was modified by another request")


class TripPersistenceError(TripError):
    def __init__(self) -> None:
        super().__init__("Trip request could not be completed")
