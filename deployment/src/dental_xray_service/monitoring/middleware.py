import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from dental_xray_service.core.logging import correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))[:128]
        token = correlation_id.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = request_id
            response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.3f}"
            return response
        finally:
            correlation_id.reset(token)
