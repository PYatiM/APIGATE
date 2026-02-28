from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.services.stats import stats
from app.core.config import settings
from app.core.security import get_current_principal, issue_dev_token, Principal
from app.services.proxy import forward_request

router = APIRouter()

class OrderItem(BaseModel):
    sku: str = Field(..., min_length=3, max_length=64)
    quantity: int = Field(..., ge=1, le=1000)


class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=64)
    items: list[OrderItem] = Field(..., min_length=1)
    note: str | None = Field(default=None, max_length=2000)


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=120)


def _resolve_dashboard_key(request: Request) -> str | None:
    return request.headers.get("x-dashboard-key") or request.query_params.get("dashboard_key")


def _require_dashboard_key(request: Request) -> None:
    if not settings.dashboard_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard disabled")
    if settings.dashboard_api_key == "CHANGE_ME_DASHBOARD_KEY":
        return
    key = _resolve_dashboard_key(request)
    if key != settings.dashboard_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid dashboard key")


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.post(settings.oauth2_token_url)
async def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if settings.env == "prod":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token endpoint disabled")
    token = issue_dev_token(form_data.username, scopes=["gateway:access"])
    return {"access_token": token, "token_type": "bearer"}


@router.get("/stats")
async def get_stats(request: Request) -> dict:
    _require_dashboard_key(request)
    snapshot = stats.snapshot()
    snapshot.update({
        "auth_required": settings.auth_required,
        "rate_limit": {
            "requests": settings.rate_limit_requests,
            "window_seconds": settings.rate_limit_window_seconds,
            "backend": settings.rate_limit_backend,
        },
        "openapi_validation": settings.openapi_validate_requests,
    })
    return snapshot


@router.get("/dashboard")
async def dashboard(request: Request) -> HTMLResponse:
    _require_dashboard_key(request)
    html_path = Path("app/templates/dashboard.html")
    html_content = html_path.read_text(encoding="utf-8")
    dashboard_key = _resolve_dashboard_key(request) or ""
    html_content = html_content.replace("{{dashboard_key}}", dashboard_key)
    return HTMLResponse(html_content)


@router.post("/v1/echo")
async def echo(
    payload: dict,
    request: Request,
    principal: Principal = Depends(get_current_principal),
):
    request.state.principal = principal
    return {"received": payload, "principal": principal.subject}


@router.post("/v1/orders")
async def create_order(
    payload: OrderCreate,
    request: Request,
    principal: Principal = Depends(get_current_principal),
):
    request.state.principal = principal
    return await forward_request(request, "/orders", principal)


@router.get("/v1/orders/{order_id}")
async def get_order(
    order_id: str,
    request: Request,
    principal: Principal = Depends(get_current_principal),
):
    request.state.principal = principal
    return await forward_request(request, f"/orders/{order_id}", principal)


@router.post("/v1/users")
async def create_user(
    payload: UserCreate,
    request: Request,
    principal: Principal = Depends(get_current_principal),
):
    request.state.principal = principal
    return await forward_request(request, "/users", principal)
