"""Request ID tracing middleware.

Generates or propagates an X-Request-ID header on every request/response.
Stores the request ID in a contextvars.ContextVar for use in logging and
downstream service calls.
"""

import contextvars
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "x-request-id"

# Context variable for request-scoped ID propagation
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    """Return current request ID from context, or None outside a request."""
    return request_id_var.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to each incoming request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)
        rid = incoming_id if incoming_id else str(uuid.uuid4())
        token = request_id_var.set(rid)
        try:
            response: Response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = rid
            return response
        finally:
            request_id_var.reset(token)
