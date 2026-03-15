import os

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk, JWTError

security = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise HTTPException(status_code=500, detail="SUPABASE_URL not configured")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{supabase_url}/auth/v1/.well-known/jwks.json"
            )
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token header")

    jwks = await _get_jwks()

    rsa_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == unverified_header.get("kid"):
            rsa_key = key_data
            break

    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find matching signing key")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience="authenticated",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload
