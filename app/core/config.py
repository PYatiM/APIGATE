import os

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Secure API Gateway(APIGATE)")
    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "False").lower() == "true"
    
    JWT_SECRET: str = os.getenv("Oauth_JWT_SECRET","dev-secret")
    JWT_SECRET: str = os.getenv("OAUTH@_ISSUER","local")
    JWT_AUDIENCE: str = os.getenv("OAUTH_AUDIENCE","gateway")
    
settings = Settings()