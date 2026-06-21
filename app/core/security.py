from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer,  SecurityScopes
from jose import JWTError, jwt
#The difference between this import and previous jwt is that this lines makes it easier to use the standard PyJWT PyJWKClient and in the previouss import its for when pyhton-jose or standard PyJWT is used
import jwt as pyjwt

from app.core.config import settings


@dataclass
class Principal:
    subject: str
    scopes: list[str]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.oauth2_token_url, auto_error=False)
jwks_client =  pyjwt.PyJWKClient(settings.oauth2_jwks_url)

def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_principal(security_scopes: SecurityScopes, request: Request, token: str = Depends(oauth2_scheme)) -> Principal:
    if not settings.auth_required:
        return Principal(subject="anonymous", scopes=["*"])

    if not token:
        _raise_unauthorized("Missing bearer token")

    try:
        #Dynamic fetching of the correct public key based on the kid header in the JWT
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"], #Enforcing Asymmetric only
            issuer=settings.oauth2_issuer,
            audience=settings.oauth2_audience,
            leeway=settings.oauth2_leeway_seconds,
        )
    
    except Exception as e:
        _raise_unauthorized(f"Invalid token : {str(e)}")
    
    redis = getattr(request.app.state, "redis", None)
    if redis:
        is_blocked = await redis.get(f"blocklist:{token}")
        if is_blocked:
            _raise_unauthorized("Token has been revoked")

    subject = payload.get("sub") or "unknown"
    scope = payload.get("scope","").split()

    for scope in security_scopes.scopes:
        if scope not in scopes and "*" not in scopes:
            raise HTTPException(
                status_code=403, 
                detail=f"Forbidden: Missing required scope '{scope}'"
            )
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
