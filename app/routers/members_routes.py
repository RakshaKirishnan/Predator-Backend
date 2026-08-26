"""Dedicated router for members management."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.members_schema import MembersResponse, UpdateMemberRequest, UpdateMemberResponse

router = APIRouter(prefix="/members", tags=["members"])


def _services(request: Request):
    return request.app.state.auth_services


@router.get("", response_model=MembersResponse)
@router.get("/", response_model=MembersResponse)
def get_members(request: Request):
    """Retrieve list of all enrolled user members."""
    data = _services(request).members_service.get_members()
    return {
        "success": True,
        "message": "Members retrieved successfully",
        "data": data,
    }


@router.put("/{user_id}", response_model=UpdateMemberResponse)
@router.patch("/{user_id}", response_model=UpdateMemberResponse)
def update_member(request: Request, user_id: str, body: UpdateMemberRequest):
    """Update member details (name, email, role). Restricted to SUPER_ADMIN only."""
    services = _services(request)

    # Extract access token from cookies or Authorization header
    access_token = request.cookies.get("access_token")
    if not access_token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1]

    # Enforcement: Require SUPER_ADMIN role
    admin_payload = services.tokens.require_super_admin(access_token)

    updated = services.members_service.update_member(
        user_id=user_id,
        name=body.name,
        email=body.email,
        role=body.role,
    )

    # Log security audit event
    try:
        services.usage_logs.create_log(
            username=str(admin_payload.get("sub") or "SUPER_ADMIN"),
            email=str(admin_payload.get("sub") or ""),
            action=f"MEMBER_UPDATED ({updated['email']} -> {updated['role']})",
            ip_address=getattr(request.state, "ip_address", "127.0.0.1"),
            user_agent=getattr(request.state, "user_agent", ""),
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "Member details updated successfully",
        "data": updated,
    }

