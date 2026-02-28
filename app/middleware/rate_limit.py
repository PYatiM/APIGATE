from __future__ import annotations

import time 
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from fastapi import HTTPException, status
from app.core.config import settings
from app.services.metrics import RATE_LIMITED_TOTAL

class LocalRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.counters: dict[tuple[str, int], int] = defaultdict(int)

    def allow(self, client_id: str) -> bool:
        if self.limit <= 0:
            return True
        window = int(time.time() // self.window_seconds)
        key = (client_id, window)
        self.counters[key] += 1
        if len(self.counters) > 5000:
            self._prune(window)
        return self.counters[key] <= self.limit

    def _prune(self, current_window: int) -> None:
        old_windows = [key for key in self.counters if key[1] < current_window - 1]
        for key in old_windows:
            self.counters.pop(key, None)
            
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.local_limiter = LocalRateLimiter(
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )
    
    async def dispatch(self, request: Request, call_next)-> Response:
        client_id = request.headers.get("x-client-id") or "unknown"
        if request.client:
            client_id = request.headers.get("x-client-id") or request.client.host

        allowed = True
        if settings.rate_limit_backend == "redis":
            redis = getattr(request.app.state, "redis", None)
            if redis is None:
                allowed = self.local_limiter.allow(client_id)
            else:
                allowed = await self._allow_redis(redis, client_id)
        else:
            allowed = self.local_limiter.allow(client_id)

        if not allowed:
            RATE_LIMITED_TOTAL.labels(client=client_id).inc()
            request.state.rate_limited = True
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": settings.rate_limit_requests,
                    "window_seconds": settings.rate_limit_window_seconds,
                },
            )
        
        return await call_next(request)
    
    async def _allow_redis(self, redis, client_id: str) -> bool:
        if settings.rate_limit_requests <= 0:
            return True
        window_key = int(time.time() // settings.rate_limit_window_seconds)
        key = f"rl:{client_id}:{window_key}"
        pipeline = redis.pipeline()
        pipeline.incr(key, 1)
        pipeline.expire(key, settings.rate_limit_window_seconds)
        count, _ = await pipeline.execute()
        return int(count) <= settings.rate_limit_requests
    
    
