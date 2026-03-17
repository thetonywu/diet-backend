import time
from collections import defaultdict

from fastapi import HTTPException, Request
from jose import jwt
from slowapi.util import get_remote_address

AUTHED_LIMIT = 20   # requests per minute for logged-in users
ANON_LIMIT = 5      # requests per minute for anonymous users

_window: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(key: str, limit: int) -> None:
    now = time.monotonic()
    timestamps = _window[key]
    # drop entries older than 60 seconds
    _window[key] = [t for t in timestamps if now - t < 60]
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
                _check_rate_limit(f"user:{sub}", AUTHED_LIMIT)
                return
        except Exception:
            pass
    ip = get_remote_address(request)
    _check_rate_limit(f"ip:{ip}", ANON_LIMIT)
