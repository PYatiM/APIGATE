from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import yaml

from pathlib import Path
from app.core.config import settings

logger = logging.getLogger("gateway.openapi")

IMPORT_ERROR: Exception | None = None

try:
    from openapi_core import Spec
except Exception as exc:  # pragma: no cover - handled by runtime deps
    Spec = None
    IMPORT_ERROR = exc
    
try:
    from openapi_core.contrib.starlette.requests import StarletteOpenAPIRequest
except Exception as exc:  # pragma: no cover
    StarletteOpenAPIRequest = None
    IMPORT_ERROR = IMPORT_ERROR or exc

try:
    from openapi_core.validation.request.validators import RequestValidator
except Exception as exc:  # pragma: no cover
    RequestValidator = None
    IMPORT_ERROR = IMPORT_ERROR or exc

class OpenAPIValidatorMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app) -> None:
        super().__init__(app)
        self.enabled = settings.openapi_validate_requests
        self.spec = None
        self.validator = None
        self.skip_paths = {
            "/health",
            "/metrics",
            "/stats",
            "/dashboard",
            "/docs",
            "/openapi.json",
            settings.oauth2_token_url,
        }

        if not self.enabled:
            return
        if Spec is None or StarletteOpenAPIRequest is None or RequestValidator is None:
            logger.warning(
                "OpenAPI validation disabled: openapi-core missing/incompatible (%s)",
                IMPORT_ERROR,
            )
            self.enabled = False
            return

        spec_path = Path(settings.openapi_spec_path)
        if not spec_path.exists():
            logger.warning("OpenAPI validation disabled: spec file not found at %s", spec_path)
            self.enabled = False
            return

        try:
            with spec_path.open("r", encoding="utf-8") as handle:
                spec_dict = yaml.safe_load(handle)
            self.spec = Spec.from_dict(spec_dict)
            self.validator = RequestValidator(self.spec)
        except Exception as exc:
            logger.warning("OpenAPI validation disabled: failed to load/parse spec - %s", exc)
            self.enabled = False    
    
    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.url.path in self.skip_paths:
            return await call_next(request)
        if request.url.path.startswith("/static/") or request.url.path == "/favicon.ico":
            return await call_next(request)

        await request.body()
        openapi_request = StarletteOpenAPIRequest(request)
        result = self.validator.validate(openapi_request)
        if result.errors:
            errors = [str(error) for error in result.errors]
            return JSONResponse(
                status_code=400,
                content={"detail": "Request validation failed", "errors": errors},
            )

        return await call_next(request)