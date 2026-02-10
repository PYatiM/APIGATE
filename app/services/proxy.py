import httpx
import os

UPSTREAM = os.getenv("UPSTREAM_BASE_URL", "http://localhost:9000")

async def forward_request(path, method, headers, body):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{UPSTREAM}{path}",
            headers=headers,
            content=body,
        )
        return response
