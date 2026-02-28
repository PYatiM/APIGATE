from __future__ import annotations

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Secure API Gateway"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8443
    log_level: str = "info"

    tls_cert_file: str = "certs/server.crt"
    tls_key_file: str = "certs/server.key"

    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_backend: str = "redis"  # redis or local

    auth_required: bool = True
    oauth2_token_url: str = "/auth/token"
    oauth2_issuer: str = "secure-gateway"
    oauth2_audience: str = "secure-gateway-clients"
    oauth2_jwt_secret: str = "ww34d2d3c235v315775wdd756d35f5m478c38nt384nf34t8634t9"
    oauth2_jwt_algorithm: str = "HS256"
    oauth2_leeway_seconds: int = 30

    upstream_base_url: AnyHttpUrl | None = None
    mock_upstream: bool = True

    openapi_spec_path: str = "specs/gateway.openapi.yaml"
    openapi_validate_requests: bool = True

    otel_service_name: str = "secure-api-gateway"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    otel_exporter_otlp_insecure: bool = True
    otel_logs_enabled: bool = True
    otel_traces_enabled: bool = True

    dashboard_enabled: bool = True
    dashboard_api_key: str = "6td468t9h1d789yhd479y978y3427nyt2o3479yf98yp09uo232m18p0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
