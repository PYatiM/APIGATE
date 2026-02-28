from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import yaml

from pathlib import Path
from app.core.config import settings

try:
    from openapi_core import Spec
    from openapi_core.contrib.starlette.requests import StarletteOpenAPIRequest
    from openapi_core.validation.request.validators import RequestValidator
except Exception:  # pragma: no cover - handled by runtime deps
    Spec = None
    StarletteOpenAPIRequest = None
    RequestValidator = None
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
        if Spec is None:
            raise RuntimeError("openapi-core is required for request validation")

        spec_path = Path(settings.openapi_spec_path)
        if not spec_path.exists():
            raise RuntimeError(f"OpenAPI spec not found at {spec_path}")

        with spec_path.open("r", encoding="utf-8") as handle:
            spec_dict = yaml.safe_load(handle)
        self.spec = Spec.from_dict(spec_dict)
        self.validator = RequestValidator(self.spec)
    
    
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
        
        response = call_next(request)
        return response