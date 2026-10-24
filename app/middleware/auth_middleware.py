"""FastAPI standalone middleware and helpers for extracting and verifying JWT tokens."""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token from cookies or Authorization header."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    return token


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts and decodes access tokens on incoming requests."""

    async def dispatch(self, request: Request, call_next):
        token = extract_token_from_request(request)
        request.state.token = token
        request.state.user = None
        request.state.user_id = None
        request.state.email = None
        request.state.role = None
        request.state.is_authenticated = False

        if token:
            try:
                services = getattr(request.app.state, "auth_services", None)
                if services and hasattr(services, "tokens"):
                    payload = services.tokens.decode_access_token(token)
                    request.state.user = payload
                    request.state.email = payload.get("sub")
                    request.state.user_id = payload.get("user_id")
                    request.state.role = str(payload.get("role") or "").upper()
                    request.state.is_authenticated = True
            except Exception as exc:
                logger.debug("AuthMiddleware token verification: %s", exc)

        response = await call_next(request)
        return response


def get_current_user(request: Request) -> Optional[dict[str, Any]]:
    """Return authenticated user payload or None."""
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> dict[str, Any]:
    """Strictly require authenticated user session."""
    user = getattr(request.state, "user", None)
    if not user:
        raise UnauthorizedError("Authentication required")
    return user


def require_admin(request: Request) -> dict[str, Any]:
    """Strictly require ADMIN or SUPER_ADMIN role."""
    user = require_auth(request)
    role = str(user.get("role") or "").upper()
    if role not in {"ADMIN", "SUPER_ADMIN"}:
        raise ForbiddenError("Admin access required")
    return user


def require_super_admin(request: Request) -> dict[str, Any]:
    """Strictly require SUPER_ADMIN role."""
    user = require_auth(request)
    role = str(user.get("role") or "").upper()
    if role != "SUPER_ADMIN":
        raise ForbiddenError("Only SUPER_ADMIN can perform this action")
    return user
