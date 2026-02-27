import httpx
from fastapi import Request, Response


async def proxy_request(request: Request, upstream_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method = request.method,
            url = upstream_url,
            headers = request.headers.raw,
            content = await request.body()
        )
        return Response(
            content = response.content,
            status_code = response.status_code,
            headers = response.headers
        )
    
