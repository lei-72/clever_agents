from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import set_request_id

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def _best_effort_route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path or request.url.path)


class RequestIdAndMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        set_request_id(request_id)

        started = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
        finally:
            elapsed = max(0.0, time.perf_counter() - started)
            path = _best_effort_route_path(request)
            method = request.method
            status_code = str(getattr(getattr(request, "state", object()), "status_code", None) or "")
            # status_code 在这里拿不到时，后面会用 response.status_code 补齐
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(elapsed)

        response.headers["X-Request-Id"] = request_id
        status = str(response.status_code)
        path = _best_effort_route_path(request)
        HTTP_REQUESTS_TOTAL.labels(method=request.method, path=path, status_code=status).inc()
        return response

