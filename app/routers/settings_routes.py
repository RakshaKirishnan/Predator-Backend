"""Router for System Settings & Email Template Array Management."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.repository.app_settings_repository import render_markdown_to_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def _services(request: Request):
    return request.app.state.auth_services


class UpdateTemplateItemRequest(BaseModel):
    subject: str
    body: str


class EmailPreviewRequest(BaseModel):
    subject: Optional[str] = None
    body: str


@router.get("/email-templates")
def list_email_templates(request: Request):
    """Retrieve all email templates from app_settings collection array."""
    services = _services(request)
    templates_data = services.app_settings.list_email_templates()
    return {
        "success": True,
        "message": "Email templates list retrieved successfully",
        "data": templates_data,
    }


@router.put("/email-templates/{template_id}")
def update_email_template(request: Request, template_id: str, body: UpdateTemplateItemRequest):
    """Update and persist specific email template in app_settings array."""
    services = _services(request)

    # Optional token verification — verify admin if token present
    access_token = request.cookies.get("access_token")
    if not access_token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1]

    if access_token:
        try:
            services.tokens.require_admin(access_token)
        except Exception as exc:
            logger.warning("Template update token check warning: %s", exc)

    saved = services.app_settings.save_email_template(
        template_key=template_id,
        subject=body.subject,
        body=body.body,
    )

    return {
        "success": True,
        "message": f"Email template '{template_id}' saved to app_settings collection",
        "data": saved,
    }


@router.post("/email-templates/reset")
def reset_email_templates(request: Request):
    """Reset email templates array to system defaults."""
    services = _services(request)

    access_token = request.cookies.get("access_token")
    if not access_token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1]

    if access_token:
        try:
            services.tokens.require_admin(access_token)
        except Exception as exc:
            logger.warning("Template reset token check warning: %s", exc)

    reset_data = services.app_settings.reset_email_templates()
    return {
        "success": True,
        "message": "Email templates reset to defaults",
        "data": reset_data,
    }


@router.post("/email-templates/preview")
def preview_email_template(body: EmailPreviewRequest):
    """Render markdown email template with sample context data for live preview."""
    sample_context = {
        "name": "Raksha",
        "email": "raksha@example.com",
        "invite_link": "http://localhost:3000/auth/accept-invite?token=sample-token-123456&email=raksha@example.com&name=Raksha",
        "expires_hours": 48,
        "ip_address": "192.168.1.105",
        "timestamp": "2026-08-24 21:45:00 UTC",
    }

    html_rendered = render_markdown_to_html(body.body, sample_context)
    
    # Substituted Markdown
    md_substituted = body.body
    for k, v in sample_context.items():
        md_substituted = md_substituted.replace(f"{{{{{k}}}}}", str(v))

    return {
        "success": True,
        "message": "Template rendered",
        "data": {
            "html_rendered": html_rendered,
            "markdown_substituted": md_substituted,
            "sample_context": sample_context,
        },
    }
