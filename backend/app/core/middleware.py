import logging
import re
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("visitlibya.request")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SENSITIVE_PATH_PREFIXES = ("/api/v1/auth", "/api/v1/trips", "/api/v1/favorites")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        try: response = await call_next(request)
        except Exception:
            log = logger.exception if self.debug else logger.error
            log("request_failed request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
            raise
        response.headers.update({"X-Request-ID": request_id, "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()"})
        if request.url.path.startswith(SENSITIVE_PATH_PREFIXES): response.headers["Cache-Control"] = "no-store"
        duration = round((time.perf_counter() - started) * 1000, 2)
        logger.info("request_completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
                    request_id, request.method, request.url.path, response.status_code, duration)
        return response
