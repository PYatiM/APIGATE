from starlette.middleware.base import BaseHTTPMiddleware
from app.services.audit import emit_audit_event


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        emit_audit_event(request, response.status_code)
        return response
