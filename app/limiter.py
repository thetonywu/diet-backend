import time
from collections import defaultdict

from fastapi import HTTPException, Request
from jose import jwt

AUTHED_LIMIT = (20, 60)       # 20 requests per 60 seconds
ANON_LIMIT = (5, 3600)        # 5 requests per hour

_window: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(key: str, limit: int, window: int) -> None:
    now = time.monotonic()
    timestamps = _window[key]
    _window[key] = [t for t in timestamps if now - t < window]
    if len(_window[key]) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _window[key].append(now)


def rate_limit(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            claims = jwt.get_unverified_claims(auth[7:])
            sub = claims.get("sub")
            if sub:
                _check_rate_limit(f"user:{sub}", *AUTHED_LIMIT)
                return
        except Exception:
            pass
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    _check_rate_limit(f"ip:{ip}", *ANON_LIMIT)
