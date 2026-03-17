import os
import time

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

ALLOWED_ALGORITHMS = ["RS256", "ES256"]

_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0
JWKS_TTL = 3600


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    if _jwks_cache is None or (time.monotonic() - _jwks_fetched_at) > JWKS_TTL:
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise HTTPException(status_code=500, detail="SUPABASE_URL not configured")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{supabase_url}/auth/v1/.well-known/jwks.json"
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch JWKS from identity provider")
            _jwks_cache = resp.json()
            _jwks_fetched_at = time.monotonic()
    return _jwks_cache


async def _verify_token(token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token header")

    token_alg = unverified_header.get("alg")
    if token_alg not in ALLOWED_ALGORITHMS:
        raise HTTPException(status_code=401, detail="Unsupported token algorithm")

    jwks = await _get_jwks()

    signing_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == unverified_header.get("kid"):
            signing_key = key_data
            break

    if not signing_key:
        raise HTTPException(status_code=401, detail="Unable to find matching signing key")

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[token_alg],
            audience="authenticated",
            issuer=f"{os.getenv('SUPABASE_URL')}/auth/v1",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return await _verify_token(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
) -> dict | None:
    if credentials is None:
        return None
    return await _verify_token(credentials.credentials)
