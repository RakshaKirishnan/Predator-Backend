"""FastAPI middleware to extract client metadata (IP address and User-Agent)."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class ClientMetadataMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract IP address
        if request.client:
            ip_address = request.client.host
        else:
            ip_address = ""

        # Handle proxy headers (e.g. X-Forwarded-For) if present
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # Get the first IP in the list
            ip_address = x_forwarded_for.split(",")[0].strip()

        # Extract User-Agent
        user_agent = request.headers.get("user-agent", "")

        # Store in request.state
        request.state.ip_address = ip_address
        request.state.user_agent = user_agent

        response = await call_next(request)
        return response
