import logging
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not configured")

    token = credentials.credentials
    try:
        unverified = jwt.get_unverified_claims(token)
        logger.info("Token claims: iss=%s aud=%s", unverified.get("iss"), unverified.get("aud"))
    except Exception as e:
        logger.error("Failed to decode unverified token: %s", e)

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        logger.error("JWT verification failed: %s", e)
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    return payload
