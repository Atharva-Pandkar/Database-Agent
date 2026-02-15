import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class CorrelationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.correlation_id_header = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract correlation ID from header or generate new one
        correlation_id = request.headers.get(self.correlation_id_header)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Process the request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.correlation_id_header] = correlation_id
        
        return response
