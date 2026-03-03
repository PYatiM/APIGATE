from __future__ import annotations

import logging

import httpx
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.telemetry import setup_telemetry
from app.middleware.openapi_validator import OpenAPIRequestValidationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.audit import AuditMiddleware
from app.services.redis import close_redis, init_redis

logger = logging.getLogger("gateway")


def create_app() -> FastAPI:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = FastAPI(title=settings.app_name, version="1.0.0")
    setup_telemetry(app)

    app.add_middleware(OpenAPIRequestValidationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuditMiddleware)

    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.on_event("startup")
    async def startup() -> None:
        try:
            app.state.redis = await init_redis()
            logger.info("Redis connection established")
        except Exception as exc:
            app.state.redis = None
            logger.warning("Redis unavailable, falling back to local rate limiting: %s", exc)

        app.state.httpx = httpx.AsyncClient()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_redis(getattr(app.state, "redis", None))
        httpx_client: httpx.AsyncClient | None = getattr(app.state, "httpx", None)
        if httpx_client:
            await httpx_client.aclose()

    return app


app = create_app()

