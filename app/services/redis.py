import redis
import os 

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def get_redis():
    try:
        return redis.from_url(REDIS_URL)
    except Exception:
        return None