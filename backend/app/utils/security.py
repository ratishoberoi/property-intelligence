import time
from collections import defaultdict, deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """Simple local rate-limiting abstraction for demos and tests."""

    def __init__(self, app, limit_per_minute: int = 240):
        super().__init__(app)
        self.limit = limit_per_minute
        self.window: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        identity = request.client.host if request.client else "unknown"
        now = time.time()
        events = self.window[identity]
        while events and now - events[0] > 60:
            events.popleft()
        if len(events) >= self.limit:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        events.append(now)
        return await call_next(request)

