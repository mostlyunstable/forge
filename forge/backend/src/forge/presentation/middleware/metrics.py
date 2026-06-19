"""Metrics collection middleware."""
from __future__ import annotations

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from forge.config.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects Prometheus metrics for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        ACTIVE_REQUESTS.inc()
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
            ).inc()
            raise
        finally:
            ACTIVE_REQUESTS.dec()

        duration = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response
