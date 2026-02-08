from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Secure API Gateway")

app.include_router(router)

@app.get("/")
def root():
    return {"status": "gateway running"}
