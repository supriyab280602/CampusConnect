import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import current_app, jsonify, request


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter keyed by client IP and route."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


auth_rate_limiter = SlidingWindowRateLimiter()


def rate_limit_auth(default_max: int = 20, default_window: int = 60):
    """Apply sliding-window rate limiting to auth endpoints when enabled."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            enabled = current_app.config.get(
                "RATELIMIT_ENABLED",
                not current_app.config.get("TESTING", False),
            )
            if not enabled:
                return f(*args, **kwargs)

            max_requests = int(current_app.config.get("RATELIMIT_MAX_REQUESTS", default_max))
            window_seconds = int(current_app.config.get("RATELIMIT_WINDOW_SECONDS", default_window))
            forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            client_ip = forwarded or request.remote_addr or "unknown"
            key = f"{request.endpoint}:{client_ip}"

            if not auth_rate_limiter.is_allowed(key, max_requests, window_seconds):
                return jsonify({
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "details": {}
                    }
                }), 429

            return f(*args, **kwargs)

        return wrapped

    return decorator
