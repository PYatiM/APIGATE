from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.audit import emit_audit_event
from app.services.metrics import REQUESTS_TOTAL, REQUEST_LATENCY_MS
from app.services.stats import stats


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            stats.record(500, duration_ms, False)
            emit_audit_event("exception", {"request_id": request_id, "path": request.url.path, "method": request.method, "error": str(exc)})
            raise
            
        duration_ms = (time.perf_counter() - start) * 1000
        rate_limited = bool(getattr(request.state, "rate_limited", False))
        stats.record(response.status_code, duration_ms, rate_limited)

        REQUESTS_TOTAL.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code),
        ).inc()
        REQUEST_LATENCY_MS.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration_ms)

        principal = getattr(request.state, "principal", None)
        emit_audit_event(
            "request",
            {
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else "unknown",
                "principal": getattr(principal, "subject", None),
                "rate_limited": rate_limited,
            },
        )

        response.headers["x-request-id"] = request_id
        response.headers.setdefault("x-content-type-options", "nosniff")
        response.headers.setdefault("x-frame-options", "DENY")
        response.headers.setdefault("referrer-policy", "no-referrer")
        response.headers.setdefault("permissions-policy", "geolocation=()")

        forwarded_proto = request.headers.get("x-forwarded-proto")
        if request.url.scheme == "https" or forwarded_proto == "https":
            response.headers.setdefault("strict-transport-security","max-age=63072000; includeSubDomains; preload",)

           
        return response
