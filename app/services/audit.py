import logging
import time
from app.services.metrics import REQUEST_COUNT,request

REQUEST_COUNT.labels(request.method, request.url.path).inc()
logger = logging.getLogger("gateway.audit")
logging.basicConfig(level=logging.INFO)


def emit_audit_event(request, status_code):
    logger.info(
        {
            "timestamp": time.time(),
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
            "status": status_code,
        }
    )
