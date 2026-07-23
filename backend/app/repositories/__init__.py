from app.repositories.category import CategoryRepository
from app.repositories.destination import DestinationRepository
from app.repositories.media import MediaRepository
from app.repositories.review import ReviewRepository
from app.repositories.search import SearchRepository
from app.repositories.user import UserRepository
from app.repositories.favorite import FavoriteRepository
from app.repositories.trip import TripRepository

__all__ = [
    "CategoryRepository",
    "DestinationRepository",
    "MediaRepository",
    "ReviewRepository",
    "SearchRepository",
    "UserRepository",
    "FavoriteRepository",
    "TripRepository",
]
