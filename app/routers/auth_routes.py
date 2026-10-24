"""
Auth routes — only 4 endpoints:

  POST /auth/signup
  POST /auth/face-login
  POST /auth/invite
  POST /auth/accept-invite
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.schemas.auth import (
    AcceptInviteRequest,
    FaceLoginRequest,
    InviteRequest,
    SignupRequest,
)

from app.core.exceptions import UnauthorizedError
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["auth"])


def _services(request: Request):
    return request.app.state.auth_services


@router.post("/signup")
def signup(request: Request, body: SignupRequest, response: Response):
    """Create account + enroll face (InsightFace) + set JWT cookies."""
    return _services(request).signup.signup(
        email=str(body.email),
        name=body.name,
        image_base64=body.image_base64,
        response=response,
        ip_address=request.state.ip_address,
        user_agent=request.state.user_agent,
    )


@router.post("/face-login")
def face_login(request: Request, body: FaceLoginRequest, response: Response):
    """Match live face image against enrolled users + set JWT cookies."""
    return _services(request).face_login.face_login(
        image_base64=body.image_base64,
        response=response,
        ip_address=request.state.ip_address,
        user_agent=request.state.user_agent,
    )


from app.middleware.auth_middleware import require_admin, require_auth, get_current_user as auth_user


@router.post("/invite")
def invite(request: Request, body: InviteRequest):
    """Admin sends SMTP invite with secure token."""
    services = _services(request)

    # Bootstrap: if no users exist yet, allow invite without admin cookie.
    if services.users.count() > 0:
        admin = require_admin(request)
        invited_by = admin.get("sub")
        inviter_role = str(admin.get("role") or "USER").upper()
    else:
        invited_by = None
        inviter_role = "SUPER_ADMIN"

    return services.invite.send_invite(
        email=str(body.email),
        name=body.name,
        role=body.role,
        invited_by=invited_by,
        inviter_role=inviter_role,
    )



@router.post("/accept-invite")
def accept_invite(request: Request, body: AcceptInviteRequest, response: Response):
    """Validate invite token + enroll face + set JWT cookies."""
    return _services(request).accept_invite.accept_invite(
        token=body.token,
        email=str(body.email),
        name=body.name,
        image_base64=body.image_base64,
        response=response,
        ip_address=request.state.ip_address,
        user_agent=request.state.user_agent,
    )


@router.post("/logout")
def logout(request: Request, response: Response):
    """Clear JWT cookies + log logout transaction."""
    ip_address = getattr(request.state, "ip_address", "127.0.0.1")
    user_agent = getattr(request.state, "user_agent", "")

    email = getattr(request.state, "email", None) or "unknown@example.com"
    username = "Unknown User"

    services = _services(request)
    if email and email != "unknown@example.com":
        user = services.users.find_by_email(email)
        if user:
            username = user.get("name") or email

    services.tokens.clear_auth_cookies(response)

    try:
        services.usage_logs.create_log(
            username=username,
            email=email,
            action="LOGOUT",
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        pass

    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
def get_current_user(request: Request):
    """Validate current access_token cookie or Bearer token and return user profile details."""
    user_payload = require_auth(request)
    email = user_payload.get("sub")
    if not email:
        raise UnauthorizedError("Invalid token payload")

    services = _services(request)
    user = services.users.find_by_email(email)
    if not user:
        raise UnauthorizedError("User record not found")

    return {
        "success": True,
        "message": "User session active",
        "data": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name") or user["email"],
            "role": user.get("role", "USER"),
        },
    }



@router.get("/dashboard-stats")
def dashboard_stats(request: Request):
    """Aggregate statistics for the dashboard cards."""
    stats = _services(request).dashboard_cards.get_cards_stats()
    return {
        "success": True,
        "message": "Stats retrieved",
        "data": stats,
    }


@router.get("/usage-logs")
def usage_logs(request: Request, page: int = 1, limit: int = 10):
    """Retrieve paginated logging audit events."""
    data = _services(request).usage_logs_service.get_logs(page=page, limit=limit)
    return {
        "success": True,
        "message": "Usage logs retrieved",
        "data": data,
    }


@router.get("/health")
def health(request: Request):
    engine = request.app.state.face_engine
    return {
        "success": True,
        "message": "ok",
        "data": {
            "engine_ready": engine.ready,
            "model": engine.config.model_name,
            "endpoints": [
                "POST /auth/signup",
                "POST /auth/face-login",
                "POST /auth/invite",
                "POST /auth/accept-invite",
                "POST /auth/logout",
                "GET /auth/dashboard-stats",
                "GET /auth/usage-logs"
            ],
        },
    }
