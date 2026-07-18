from fastapi import APIRouter

from app.api.v1.endpoints.destinations import router as destinations_router


api_router = APIRouter()
api_router.include_router(destinations_router)
