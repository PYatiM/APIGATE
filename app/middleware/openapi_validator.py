from starlette.middleware.base import BaseHTTPMiddleware

class OpenAPIValidatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # placeholder - full validation added later
        response = call_next(request)
        return response