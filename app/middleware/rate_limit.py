import time 
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, status

requests_log = {}

RATE_LIMIT = 20
WINDOW = 60

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        history = requests_log.get(client_ip, [])
        history = [t for t in history if now - t < WINDOW]

        if len(history) >= RATE_LIMIT:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        
        history.append(now)
        requests_log[client_ip] = history
        
        return await call_next(request)