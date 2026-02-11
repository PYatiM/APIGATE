import logging
import time

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
