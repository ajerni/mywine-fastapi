from time import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from os import getenv
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = getenv("JWT_SECRET")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable is not set")
ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token has expired
        if payload.get("exp") and time() > payload["exp"]:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 