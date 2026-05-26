# APIGATE — Secure API Gateway

A production-oriented API Gateway built with FastAPI, implementing JWT authentication,
OpenAPI request validation, Redis-backed rate limiting, structured audit logging,
Prometheus metrics, and distributed tracing via OpenTelemetry.

Designed to demonstrate secure gateway architecture principles applicable to backend
and security engineering roles.

---

## What It Does

- **JWT Authentication** — validates OAuth2 Bearer tokens on all protected routes; configurable issuer, audience, and clock leeway
- **OpenAPI Request Validation** — validates every incoming request against a typed OpenAPI 3.0 spec before it reaches route handlers
- **Rate Limiting** — Redis-backed sliding window rate limiter with automatic local fallback when Redis is unavailable
- **Audit Logging** — structured JSON audit events emitted on every request; OTLP-ready for log shipping
- **Prometheus Metrics** — request count, latency histograms, rate-limit counters exposed at `/metrics`
- **OpenTelemetry Tracing** — distributed traces and logs exported via OTLP to a configurable collector
- **Upstream Proxy** — forwards authenticated requests to a configurable upstream service with hop-by-hop header filtering and graceful error handling
- **Security Headers** — `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and conditional HSTS on every response
- **Operational Dashboard** — live request stats, latency percentiles, and gateway configuration via a key-protected dashboard UI
- **Mock Upstream Mode** — full gateway functionality without a real upstream service; useful for development and demos

---

## Architecture

```
Client Request
      ↓
AuditMiddleware          (assigns request-id, records latency + metrics, emits audit event)
      ↓
RateLimitMiddleware      (Redis or local sliding window; returns 429 if exceeded)
      ↓
OpenAPIRequestValidationMiddleware  (validates against gateway.openapi.yaml; returns 400 if invalid)
      ↓
Route Handler            (JWT auth via Depends; Pydantic model validation)
      ↓
Proxy / Mock Upstream    (forwards to upstream_base_url or returns mock response)
      ↓
Response + Security Headers
```

---

## Project Structure

```
APIGATE/
├── app/
│   ├── api/
│   │   └── routes.py              # All route definitions, token endpoint, dashboard
│   ├── core/
│   │   ├── config.py              # Pydantic Settings — all configuration via env vars
│   │   ├── security.py            # JWT validation, Principal dataclass, dev token issuance
│   │   └── telemetry.py           # OpenTelemetry setup (traces + logs); graceful if missing
│   ├── middleware/
│   │   ├── audit.py               # Request timing, Prometheus counters, audit event emission, security headers
│   │   ├── rate_limit.py          # Redis and local rate limiter with async locking
│   │   └── openapi_validator.py   # OpenAPI spec-based request validation
│   ├── services/
│   │   ├── audit.py               # Structured JSON audit log emission
│   │   ├── metrics.py             # Prometheus Counter and Histogram definitions
│   │   ├── proxy.py               # Async upstream forwarding with error handling
│   │   ├── redis.py               # Redis client init and teardown
│   │   └── stats.py               # In-memory approximate request statistics
│   ├── static/                    # Frontend assets (CSS, JS)
│   ├── templates/                 # Jinja-style HTML templates (index, dashboard)
│   └── main.py                    # App factory, middleware registration, lifecycle events
├── specs/
│   └── gateway.openapi.yaml       # OpenAPI 3.0 contract used for request validation
├── infra/
│   └── otel-collector.yaml        # OpenTelemetry Collector configuration
├── tests/
│   ├── conftest.py                # Test environment setup (disables auth, Redis, OTel)
│   └── test_health.py             # Health and echo endpoint tests
├── .env.example                   # Template for environment configuration
├── docker-compose.yml             # Full stack: gateway + Redis + OTel Collector
├── Dockerfile                     # Multi-stage build; non-root runtime user
└── requirements.txt               # Pinned production dependencies
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)

---

### Quick Start with Docker (Recommended)

**1. Clone the repository**
```bash
git clone https://github.com/PYatiM/APIGATE.git
cd APIGATE
```

**2. Create your environment file**
```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
```
OAUTH2_JWT_SECRET=your-strong-secret-here
DASHBOARD_API_KEY=your-dashboard-key-here
```

**3. Build and start the full stack**
```bash
docker compose build --no-cache app
docker compose up -d
docker compose logs -f app
```

**4. Verify it is running**

| Endpoint | URL |
|----------|-----|
| Console UI | http://localhost:8000/ |
| Health check | http://localhost:8000/health |
| API docs | http://localhost:8000/docs |
| Prometheus metrics | http://localhost:8000/metrics |
| Dashboard | http://localhost:8000/dashboard?dashboard_key=`<your key>` |

---

### Local Development (Without Docker)

**1. Create and activate a virtual environment**
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\Activate.ps1
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**
```bash
cp .env.example .env
# Edit .env with your values
```

**4. Start Redis** (required for Redis-backed rate limiting)
```bash
docker compose up -d redis
```

**5. Run the gateway**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## API Usage

### Step 1 — Obtain a Development Token

> The `/auth/token` endpoint is available in non-production environments only
> (`ENV != prod`). In production, integrate your own identity provider.

```bash
# JSON body
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "dev-user"}'

# Form data also accepted
curl -X POST http://localhost:8000/auth/token \
  -d "username=dev-user"
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Step 2 — Call a Protected Route

```bash
export TOKEN="eyJ..."   # paste your token

# Echo endpoint
curl -X POST http://localhost:8000/v1/echo \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hello": "world"}'

# Create an order
curl -X POST http://localhost:8000/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cust-001", "items": [{"sku": "ITEM-A", "quantity": 2}]}'

# Get an order
curl http://localhost:8000/v1/orders/order-123 \
  -H "Authorization: Bearer $TOKEN"
```

### PowerShell Equivalent

```powershell
# Get token
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/token" `
  -ContentType "application/json" `
  -Body '{"username":"dev-user"}').access_token

# Call protected endpoint
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/v1/echo" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"hello":"world"}'
```

---

## Configuration

All configuration is via environment variables (or `.env` file). Copy `.env.example`
to get started.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Secure API Gateway` | Application name |
| `ENV` | `dev` | Environment (`dev` / `prod`). `prod` disables token endpoint. |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8443` | Bind port |
| `LOG_LEVEL` | `info` | Logging level |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_REQUIRED` | `true` | Enable/disable JWT enforcement |
| `OAUTH2_JWT_SECRET` | — | **Required.** Secret key for HS256 JWT signing |
| `OAUTH2_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `OAUTH2_ISSUER` | `secure-gateway` | Expected JWT issuer (`iss` claim) |
| `OAUTH2_AUDIENCE` | `secure-gateway-clients` | Expected JWT audience (`aud` claim) |
| `OAUTH2_TOKEN_URL` | `/auth/token` | Dev token endpoint path |
| `OAUTH2_LEEWAY_SECONDS` | `30` | Clock skew tolerance for token validation |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_BACKEND` | `redis` | `redis` or `local` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `RATE_LIMIT_REQUESTS` | `100` | Requests allowed per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window duration in seconds |

### Upstream Proxy

| Variable | Default | Description |
|----------|---------|-------------|
| `UPSTREAM_BASE_URL` | — | Target upstream service URL |
| `MOCK_UPSTREAM` | `true` | Return mock responses instead of forwarding |

### OpenAPI Validation

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAPI_SPEC_PATH` | `specs/gateway.openapi.yaml` | Path to OpenAPI spec |
| `OPENAPI_VALIDATE_REQUESTS` | `true` | Enable/disable request validation |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_SERVICE_NAME` | `secure-api-gateway` | Service name in traces/logs |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTel Collector endpoint |
| `OTEL_TRACES_ENABLED` | `true` | Enable distributed tracing |
| `OTEL_LOGS_ENABLED` | `true` | Enable OTel log export |

### Dashboard

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_ENABLED` | `true` | Enable the dashboard route |
| `DASHBOARD_API_KEY` | — | **Required.** Key to protect dashboard access |

---

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests run with auth disabled, local rate limiting, and OTel mocked out — no
external services required.

---

## Observability Stack

The `docker-compose.yml` includes a full observability stack:

- **Prometheus** — scrape `/metrics` at `http://localhost:8000/metrics`
- **OpenTelemetry Collector** — receives traces and logs via OTLP at port 4318;
  configured in `infra/otel-collector.yaml`

To add a Grafana/Jaeger backend, extend `docker-compose.yml` and point the
collector exporters at your stack.

---

## Security Notes

- The `/auth/token` endpoint is a **development convenience only**. Disable it in
  production by setting `ENV=prod`.
- JWT secrets and dashboard keys must be set via environment variables — never
  committed to source control.
- In production, place the gateway behind a TLS-terminating reverse proxy (nginx,
  Caddy, AWS ALB) or configure the `TLS_CERT_FILE` / `TLS_KEY_FILE` settings for
  direct TLS termination.
- All responses include `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer`, and HSTS (when running over HTTPS).

---

## Screenshots

### Fast API Dashboard
![img](img/1.png)

### Custom Interface
![img](img/2.png)

