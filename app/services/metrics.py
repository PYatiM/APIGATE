from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("gateway_requests_total", "Total requests through the gateway", ["method", "path","status"],)

REQUEST_LATENCY_MS = Histogram("gateway_request_latency_ms", "Gateway request latency in milliseconds", ["method", "path"],)

RATE_LIMITED_TOTAL = Counter("gateway_rate_limited_total", "Rate limited requests", ["client"],)

AUDIT_EVENTS_TOTAL = Counter("gateway_audit_events_total", "Audit log events", ["event_type"],)