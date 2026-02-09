import jwt
from fastapi import HTTPException, status
from app.core.config import settings

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, 
                             settings.JWT_SECRET, 
                             algorithms=["HS256"], 
                             audience=settings.JWT_AUDIENCE,
                             issuer=settings.JWT_ISSUER,
                             )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")