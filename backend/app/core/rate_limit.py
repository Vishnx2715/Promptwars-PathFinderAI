"""
Simple in-memory token-bucket rate limiter for key endpoints.
No external dependencies required; works with FastAPI.
"""
import time
from collections import defaultdict
from typing import Optional, Tuple
from fastapi import HTTPException, status, Request
import threading

# (identifier, action) -> list of timestamps
_buckets: dict = defaultdict(list)
_lock = threading.Lock()


def check_rate_limit(
    identifier: str,
    action: str,
    max_calls: int,
    window_seconds: int
) -> Tuple[bool, Optional[str]]:
    """
    Check if the given identifier is within the rate limit for an action.
    Returns (allowed, error_message).
    """
    now = time.time()
    key = f"{identifier}:{action}"

    with _lock:
        timestamps = _buckets[key]
        cutoff = now - window_seconds
        # Prune old timestamps
        _buckets[key] = [t for t in timestamps if t > cutoff]
        current = len(_buckets[key])

        if current >= max_calls:
            retry = int(window_seconds - (now - _buckets[key][0]))
            return False, f"Rate limit exceeded. Try again in {max(retry, 1)} seconds."

        _buckets[key].append(now)
        return True, None


def rate_limit_dependency(action: str, max_calls: int, window_seconds: int):
    """
    FastAPI dependency factory for rate limiting by user id or IP.
    """
    async def _dep(request: Request, current_user=None):
        identifier = "anonymous"
        if current_user:
            identifier = f"user:{current_user.id}"
        else:
            # Fallback to client IP
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                identifier = f"ip:{forwarded.split(',')[0].strip()}"
            else:
                identifier = f"ip:{request.client.host if request.client else 'unknown'}"

        allowed, err = check_rate_limit(identifier, action, max_calls, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=err or "Rate limit exceeded."
            )
    return _dep


def get_client_identifier(request: Request, user_id: Optional[int] = None) -> str:
    if user_id:
        return f"user:{user_id}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"
