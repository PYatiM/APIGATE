import os

os.environ.setdefault("AUTH_REQUIRED","false")
os.environ.setdefault("RATE_LIMIT_BACKEND","local")
os.environ.setdefault("OPENAPI_VALIDATE_REQUESTS","false")
os.environ.setdefault("DASHBOARD_ENABLED","false")
os.environ.setdefault("MOCK_UPSTREAM","true")
os.environ.setdefault("OTEL_LOGS_ENABLED","false")
os.environ.setdefault("OTEL_TRACES_ENABLED","false")
