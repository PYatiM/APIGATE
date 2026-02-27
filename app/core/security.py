from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings


@dataclass
class Principal:
    subject: str
    scopes: list[str]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.oauth2_token_url, auto_error=False)


def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_principal(token: str = Depends(oauth2_scheme)) -> Principal:
    if not settings.auth_required:
        return Principal(subject="anonymous", scopes=["*"])

    if not token:
        _raise_unauthorized("Missing bearer token")

    try:
        payload = jwt.decode(
            token,
            settings.oauth2_jwt_secret,
            algorithms=[settings.oauth2_jwt_algorithm],
            issuer=settings.oauth2_issuer,
            audience=settings.oauth2_audience,
            options={"verify_aud": True},
            leeway=settings.oauth2_leeway_seconds,
        )
    except JWTError:
        _raise_unauthorized("Invalid token")

    subject = payload.get("sub") or "unknown"
    scope = payload.get("scope") or ""
    scopes = [value for value in scope.split() if value]
    return Principal(subject=subject, scopes=scopes)


def issue_dev_token(username: str, scopes: list[str] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.oauth2_issuer,
        "aud": settings.oauth2_audience,
        "sub": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "scope": " ".join(scopes or []),
    }
    return jwt.encode(payload, settings.oauth2_jwt_secret, algorithm=settings.oauth2_jwt_algorithm)
