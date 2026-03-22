import time
import asyncio
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. For prod, swap this with Redis."""

    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.window = 60  # seconds
        self._store: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        # Skip health checks from rate limiting
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        async with self._lock:
            hits = self._store[ip]
            # Drop timestamps outside the current window
            self._store[ip] = [t for t in hits if now - t < self.window]

            if len(self._store[ip]) >= self.rpm:
                retry_after = int(self.window - (now - self._store[ip][0]))
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Try again in {retry_after}s."},
                    headers={"Retry-After": str(retry_after)},
                )

            self._store[ip].append(now)

        return await call_next(request)
