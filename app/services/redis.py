from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import settings


async def init_redis() -> Redis:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    await client.ping()
    return client


async def close_redis(client: Redis | None) -> None:
    if client is None:
        return
    await client.close()