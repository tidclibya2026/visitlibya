from fastapi import APIRouter, Response, status
from app.db.health import check_database_connection, check_postgis, migration_is_current

router = APIRouter(prefix="/health", tags=["System"])


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness(response: Response) -> dict[str, str]:
    if (
        not check_database_connection()
        or not check_postgis()
        or not migration_is_current()
    ):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}


@router.get("/db")
def database_health(response: Response) -> dict[str, str]:
    if not check_database_connection() or not check_postgis():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}


@router.get("")
def compatibility_health(response: Response) -> dict[str, str]:
    """Compatibility alias with readiness semantics."""
    return readiness(response)
