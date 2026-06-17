from __future__ import annotations

import time 
import asyncio
import uuid
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from cachetools import TTLCache

from app.core.config import settings
from app.services.metrics import RATE_LIMITED_TOTAL

class LocalRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.counters = TTLCache(maxsize=10000, ttl=window_seconds)
        self._lock = asyncio.Lock()

    async def allow(self, client_id: str) -> bool:
        if self.limit <= 0:
            return True
        async with self._lock:
            current_count = self.counters.get(client_id,0)
            if current_count >= self.limit:
                return False
            self.counters[client_id] = current_count + 1
            return True

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
                allowed = await self.local_limiter.allow(client_id)
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
        now = time.time()
        window_start = now - settings.rate_limit_window_seconds
        
        key = f"rl:slide:{client_id}"
        member = f"{now}-{uuid.uuid4().hex}" 
        
        pipeline = redis.pipeline()
        pipeline.zremrangebyscore(key, "-inf", window_start) 
        pipeline.zadd(key, {member: now}) 
        pipeline.zcard(key)
        pipeline.expire(key, settings.rate_limit_window_seconds) 
        
        results = await pipeline.execute()
        request_count = results[2]
        
        return int(request_count) <= settings.rate_limit_requests
    
    
