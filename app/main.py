from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.middleware.openapi_validator import OpenAPIValidatorMiddleware

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)
app.add_middleware(OpenAPIValidatorMiddleware)

@app.get("/")
def root():
    return {"status": "gateway running"}
