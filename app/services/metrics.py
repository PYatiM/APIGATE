from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST # type: ignore

REQUEST_COUNT = Counter("gateway_requests_total", "Total requests", ["method", "path"])
