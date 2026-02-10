from fastapi import APIRouter, Request
from app.services.proxy import forward_request

router = APIRouter()
@router.post("/v1/echo")
async def echo(request: Request):
    body = await request.body()
    response = await forward_request(
        path="/echo",
        method="POST",
        headers=dict(request.headers),
        body=body
    )
    return response.json()

@router.get("/health")
def health_check():
    return {"status": "ok"}
