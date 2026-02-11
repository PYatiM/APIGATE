from fastapi import APIRouter, Request,Response
from app.services.proxy import forward_request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST # type: ignore

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


@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)