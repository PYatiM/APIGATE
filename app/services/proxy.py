from __future__ import annotations

from typing import Iterable

import httpx
from fastapi import Request
from fastapi.responses import Response, JSONResponse, StreamingResponse
from httpx import TimeoutException, HTTPStatusError, RequestError

from app.core.config import settings
from app.core.security import Principal

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

def _filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    filtered: dict[str, str] = {}
    for key, value in headers:
        if key.lower() in HOP_BY_HOP_HEADERS:
            continue
        filtered[key] = value
    return filtered

async def forward_request(request: Request, upstream_path: str, principal: Principal) -> Response:
    if settings.mock_upstream or settings.upstream_base_url is None:
        body = None
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.json()
            except Exception:
                body = None
        return JSONResponse(
            {
                "mock": True,
                "path": upstream_path,
                "method": request.method,
                "principal": principal.subject,
                "body": body,
            }
        )
        
    client: httpx.AsyncClient = request.app.state.httpx
    url = f"{settings.upstream_base_url}{upstream_path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers["x-principal-sub"] = principal.subject
    headers["x-request-id"] = request.state.request_id
        
     async def request_streamer():
        async for chunk in request.stream():
            yield chunk
    req = client.build_request(
        request.method,
        url,
        params=request.query_params,
        headers=headers,
        content=request_streamer(),
    )
        
    try:
        # Stream the response back to the client
        response = await client.send(req, stream=True, timeout=10.0)
    except TimeoutException:
        return JSONResponse(status_code=504, content={"detail":"Upstream timed out"})
    except RequestError as exc:
        return JSONResponse(status_code=502, content={"detail":"Upstream unreachable"})
    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        headers=_filter_headers(response.headers.items()),
        media_type=response.headers.get("content-type")
    )
    
