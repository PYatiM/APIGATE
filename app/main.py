from fastapi import FastAPI

app = FastAPI(title="Secure API Gateway")

@app.get("/")
def root():
    return {"status": "gateway running"}
