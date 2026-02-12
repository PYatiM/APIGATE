from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.middleware.openapi_validator import OpenAPIValidatorMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.audit import AuditMiddleware

app = FastAPI(title="Secure API Gateway")

app.include_router(router)
app.add_middleware(OpenAPIValidatorMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)

@app.get("/")
def root():
    return {"status": "gateway running"}
