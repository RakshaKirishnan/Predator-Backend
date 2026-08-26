"""POST /auth/invite — create token + SMTP email with fallback link generation."""

from __future__ import annotations

from urllib.parse import urlencode

from app.config import FaceAuthConfig
from app.core.exceptions import UserAlreadyExistsError
from app.services.email.smtp_sender import SmtpEmailSender
from app.services.repository.app_settings_repository import (
    AppSettingsRepository,
    render_markdown_to_html,
)
from app.services.repository.invite_repository import InviteRepository
from app.services.repository.user_repository import UserRepository


class InviteService:
    def __init__(
        self,
        *,
        config: FaceAuthConfig,
        users: UserRepository,
        invites: InviteRepository,
        app_settings: AppSettingsRepository | None = None,
        email_sender: SmtpEmailSender,
    ):
        self.config = config
        self.users = users
        self.invites = invites
        self.app_settings = app_settings
        self.email_sender = email_sender

    def send_invite(
        self,
        *,
        email: str,
        name: str,
        role: str = "USER",
        invited_by: str | None = None,
        inviter_role: str = "SUPER_ADMIN",
    ) -> dict:
        target_role = str(role or "USER").strip().upper()
        inviter_role_clean = str(inviter_role or "SUPER_ADMIN").strip().upper()

        if target_role == "SUPER_ADMIN" and inviter_role_clean != "SUPER_ADMIN":
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Only SUPER_ADMIN users can issue invitations for SUPER_ADMIN role.")

        email_l = email.strip().lower()
        if self.users.find_by_email(email_l):
            raise UserAlreadyExistsError(f"User with email '{email_l}' is already registered in the system.")

        invite = self.invites.create_invite(
            email=email_l,
            name=name,
            role=target_role,
            invited_by=invited_by,
        )


        link = self._build_invite_link(invite["token"], invite["email"], invite["name"])
        
        # Load stored template from app_settings collection
        template_info = (
            self.app_settings.get_email_template_by_key("registration")
            if self.app_settings
            else {
                "subject": "You're invited — complete face signup",
                "body": "# You're invited to PREDATOR Console\n\nHi {{name}},\n\nYou have been invited to create your account using facial biometric authentication.\n\n[Accept Invitation & Register Face]({{invite_link}})\n\n*This invitation link expires in {{expires_hours}} hours.*",
            }
        )


        subject = template_info.get("subject") or "You're invited — complete face signup"
        markdown_src = template_info.get("body") or ""


        context = {
            "name": invite["name"] or "there",
            "email": invite["email"],
            "invite_link": link,
            "expires_hours": self.config.invite_ttl_hours,
        }

        html = render_markdown_to_html(markdown_src, context)

        email_sent = True
        email_error = None
        try:
            self.email_sender.send_html(
                to_email=email_l,
                subject=subject,
                html_body=html,
            )
        except Exception as exc:  # noqa: BLE001
            email_sent = False
            email_error = str(exc)

        return {
            "success": True,
            "status_code": 200,
            "message": "Invitation sent successfully via email." if email_sent else "Invitation link generated (SMTP limit exceeded).",
            "data": {
                "email": email_l,
                "name": invite["name"],
                "role": invite["role"],
                "invite_link": link,
                "email_sent": email_sent,
                "email_error": email_error,
                "expires_at": invite["expires_at"].isoformat(),
            },
        }

    def _build_invite_link(self, token: str, email: str, name: str = "") -> str:
        base = self.config.invite_link_base.rstrip("/")
        query_params = {"token": token, "email": email}
        if name:
            query_params["name"] = name
        query = urlencode(query_params)
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}{query}"

