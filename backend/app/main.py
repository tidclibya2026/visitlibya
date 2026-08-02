from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, settings
from app.core.logging import configure_logging
from app.core.middleware import SecurityHeadersMiddleware
from app.db.session import dispose_engine


def create_app(config: Settings = settings) -> FastAPI:
    configure_logging(config)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        dispose_engine()

    application = FastAPI(
        title=config.app_name, version=config.app_version,
        description="National tourism API for Visit Libya.",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_redoc else None,
        openapi_url="/openapi.json" if config.enable_openapi else None,
        debug=config.debug, lifespan=lifespan,
    )
    application.add_middleware(SecurityHeadersMiddleware, debug=config.debug)
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=config.trusted_hosts)
    application.add_middleware(
        CORSMiddleware, allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    application.include_router(health_router)
    application.include_router(api_router, prefix=config.api_prefix)

    @application.exception_handler(Exception)
    async def unhandled_exception(request: Request, _: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload: dict[str, str] = {"detail": "Internal server error"}
        if request_id: payload["request_id"] = request_id
        return JSONResponse(status_code=500, content=payload)

    @application.get("/")
    def root() -> dict[str, str]:
        return {"service": config.app_name, "status": "running", "health": "/health/live"}

    return application


app = create_app()
