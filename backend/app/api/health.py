from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.db.health import check_database_connection


router = APIRouter(
    prefix="/health",
    tags=["System"],
)


@router.get("")
def health_check():
    database_connected = check_database_connection()

    if not database_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "service": settings.app_name,
                "database": "disconnected",
            },
        )

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": "connected",
    }