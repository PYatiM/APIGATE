# Secure api Gateway (APIGATE)

Production-oriented API Gateway built with FastAPI, implementing authentication, request validation, rate limiting, structured audit logging, metrics exposure, and observability via OpenTelemetry.

This project is designed to demonstrate secure gateway architecture principles suitable for backend and security engineering roles.

## What It Does

- Verifies OAuth2 JWT tokens
- Validates requests against OpenAPI spec
- Applies rate limiting (Redis or local fallback)
- Emits audit logs (OTLP-ready)
- Exposes Prometheus metrics
- Provides basic operational dashboard
- Supports TLS

## Architecture (Simple Show)

Client → Gateway → Middleware Stack → Upstream Service

## Middleware order

- OpenAPI validation
- Rate limiting
- JWT authentication
- Proxy to upstream
- Audit logging + metrics

## Quick Start (Local Setup)

1️⃣ Clone & Setup Environment
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

2️⃣ Configure Environment

Copy:
    cp .env.example .env

### Minimum required fields

    AUTH_REQUIRED=true
    OAUTH2_JWT_SECRET=devsecret
    REDIS_URL=redis://localhost:6379
    UPSTREAM_BASE_URL=http://localhost:9000

3️⃣ Start Redis (Required for rate limiting)
    docker-compose up -d

4️⃣ Run the Gateway
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Access:

    http://localhost:8000
    
## TLS (Optional for Local)

Generate self-signed cert:

    mkdir certs
    openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout certs/server.key \
    -out certs/server.crt \
    -days 365 \
    -subj "/CN=localhost"

Run with TLS:

    uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile certs/server.key \
    --ssl-certfile certs/server.crt
    
## Authentication

The gateway expects:
    Authorization: Bearer <YOUR_JWT_TOKEN>

For local development only:
    POST /auth/token

Example:

    curl -X POST http://localhost:8000/auth/token \
    -d "username=dev-user&password=dev"

Use returned token in protected routes.

## OpenAPI Validation

Defined in:
    specs/gateway.openapi.yaml

To disable validation:
    OPENAPI_VALIDATE_REQUESTS=false

## Rate Limiting

Default: Redis-backed fixed window.

Control with:

    RATE_LIMIT_REQUESTS=100
    RATE_LIMIT_WINDOW_SECONDS=60

Fallback:

    RATE_LIMIT_BACKEND=local

## Observability (Optional but Recommended)

Integrated with OpenTelemetry.

Set:

    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
    OTEL_TRACES_ENABLED=true
    OTEL_LOGS_ENABLED=true

Start local collector:

    docker-compose up -d

- Telemetry can be forwarded to SIEM, Grafana, Datadog, etc.

## Metrics & Dashboard

Metrics endpoint:

    GET /metrics

Dashboard:

    GET /dashboard

If protected:

    /dashboard?dashboard_key=YOUR_KEY

## Testing

Run:
    pytest

    (might face some issues -> Redis not running - {Gateway falls back to local limiter.}, JWT failing - {Check secret, issuer, audience.}, OpenAPI errors - {Verify gateway.openapi.yaml schema}, OTLP export errors - {Confirm collector endpoint} )
