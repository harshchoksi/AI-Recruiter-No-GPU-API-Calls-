"""
Request/response logging middleware with latency tracking.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        elapsed_ms = (time.time() - start_time) * 1000

        # Add latency header
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"

        print(
            f"{request.method} {request.url.path} -> {response.status_code} "
            f"({elapsed_ms:.0f}ms)"
        )
        return response
