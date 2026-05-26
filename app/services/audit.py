from __future__ import annotations

import logging

from app.services.metrics import AUDIT_EVENTS_TOTAL, REQUEST_COUNT
from typing import Any

logger = logging.getLogger("audit")


def emit_audit_event(event_type: str, payload: dict[str, Any]) -> None:
    AUDIT_EVENTS_TOTAL.labels(event_type=event_type).inc()
    log_record = {}"event_type": event_type, **payload}
    logger.info(json.dumps(log_record, default=str))