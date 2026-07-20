from fastapi import APIRouter

from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.destinations import router as destinations_router
from app.api.v1.endpoints.media import router as media_router
from app.api.v1.endpoints.reviews import router as reviews_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.auth import router as auth_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(destinations_router)
api_router.include_router(media_router)
api_router.include_router(reviews_router)
api_router.include_router(search_router)
