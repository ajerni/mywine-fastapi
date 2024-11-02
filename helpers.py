from time import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from os import getenv
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

load_dotenv()

JWT_SECRET_KEY = getenv("JWT_SECRET")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable is not set")
ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        logging.info(f"Attempting to verify token: {token[:10]}...")
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        logging.info(f"Token decoded successfully: {payload}")
        
        # Check if token has expired
        if payload.get("exp") and time() > payload["exp"]:
            logging.error("Token has expired")
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except JWTError as e:
        logging.error(f"JWT Error during token verification: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logging.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_admin_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_admin_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        ) 