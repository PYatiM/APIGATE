from __future__ import annotations

import logging

from app.services.metrics import AUDIT_EVENTS_TOTAL, REQUESTS_TOTAL
import json
from typing import Any

logger = logging.getLogger("audit")

SENSITIVE_KEYS = {"password", "token", "authorization", "x-dashboard-key", "secret", "access_token"}
def redact_payload(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else redact_payload(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [redact_payload(item) for item in data]
    return data

def emit_audit_event(event_type: str, payload: dict[str, Any]) -> None:
    AUDIT_EVENTS_TOTAL.labels(event_type=event_type).inc()

    safe_payload =redact_payload(payload)
    log_record = {"event_type": event_type, **safe_payload}
    logger.info(json.dumps(log_record, default=str))