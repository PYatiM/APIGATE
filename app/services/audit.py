import logging

from app.services.metrics import AUDIT_EVENTS_TOTAL, REQUEST_COUNT
from typing import Any

logger = logging.getLogger("audit")


def emit_audit_event(event_type: str, payload: dict[str, Any]) -> None:
    AUDIT_EVENTS_TOTAL.labels(event_type=event_type).inc()
    logger.info("audit_event", extra={"event_type": event_type, "payload": payload})