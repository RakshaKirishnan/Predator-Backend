"""POST /auth/face-login — InsightFace 1:N match + issue cookies & security alerts."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import Response

from app.core.timezone import format_ist_display
from app.core.exceptions import FaceLoginFailedError
from app.services.auth.face_embedding_service import FaceEmbeddingService
from app.services.auth.token_service import TokenService
from app.services.matching.compare import compare_embeddings
from app.services.repository.user_repository import UserRepository
from app.services.repository.usage_log_repository import UsageLogRepository
from app.services.repository.app_settings_repository import AppSettingsRepository, render_markdown_to_html
from app.services.email.smtp_sender import SmtpEmailSender

logger = logging.getLogger(__name__)


class FaceLoginService:
    # Class-level counter for consecutive failed scan tracking per IP address
    _failed_attempts: dict[str, int] = {}

    def __init__(
        self,
        *,
        users: UserRepository,
        face_embeddings: FaceEmbeddingService,
        tokens: TokenService,
        match_threshold: float,
        usage_logs: UsageLogRepository,
        app_settings: Optional[AppSettingsRepository] = None,
        email_sender: Optional[SmtpEmailSender] = None,
    ):
        self.users = users
        self.face_embeddings = face_embeddings
        self.tokens = tokens
        self.match_threshold = match_threshold
        self.usage_logs = usage_logs
        self.app_settings = app_settings
        self.email_sender = email_sender

    def face_login(
        self,
        *,
        image_base64: str,
        response: Response,
        ip_address: str = "127.0.0.1",
        user_agent: str = "",
    ) -> dict:
        ip_key = ip_address.strip() or "127.0.0.1"

        try:
            live = self.face_embeddings.from_image_base64(image_base64)
            candidates = self.users.list_with_embeddings()
        except Exception as exc:
            self._handle_login_failure(
                image_base64=image_base64,
                ip_address=ip_key,
                user_agent=user_agent,
                reason=f"Face embedding extraction failed: {exc}",
            )
            raise FaceLoginFailedError("User not registered — Unable to extract facial embedding") from exc

        if not candidates:
            self._handle_login_failure(
                image_base64=image_base64,
                ip_address=ip_key,
                user_agent=user_agent,
                reason="No enrolled users in system",
            )
            raise FaceLoginFailedError("User not registered — No enrolled users in database")

        best_user = None
        best_match = None
        for user in candidates:
            stored = user.get("face_embedding") or []
            if not stored:
                continue
            result = compare_embeddings(
                live.embedding,
                stored,
                threshold=self.match_threshold,
            )
            if best_match is None or result.similarity > best_match.similarity:
                best_match = result
                best_user = user

        if best_user is None or best_match is None or not best_match.matched:
            self._handle_login_failure(
                image_base64=image_base64,
                ip_address=ip_key,
                user_agent=user_agent,
                reason="Face similarity below threshold",
            )
            raise FaceLoginFailedError("User not registered")

        # Successful login -> reset failure counter
        FaceLoginService._failed_attempts[ip_key] = 0

        tokens_dict = self.tokens.set_auth_cookies(
            response,
            email=best_user["email"],
            role=best_user.get("role") or "USER",
            user_id=best_user["user_id"],
        )

        try:
            self.usage_logs.create_log(
                username=best_user.get("name") or best_user["email"],
                email=best_user["email"],
                action="LOGIN",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            pass  # Non-blocking log persistence

        return {
            "success": True,
            "status_code": 200,
            "message": "Face verified successfully",
            "data": {
                "user_id": best_user["user_id"],
                "email": best_user["email"],
                "name": best_user.get("name"),
                "role": best_user.get("role"),
                "similarity": best_match.similarity,
                "match_percentage": best_match.match_percentage,
                "access_token": tokens_dict.get("access_token"),
            },
        }

    def _handle_login_failure(
        self,
        *,
        image_base64: str,
        ip_address: str,
        user_agent: str,
        reason: str,
    ) -> None:
        curr_fails = FaceLoginService._failed_attempts.get(ip_address, 0) + 1
        FaceLoginService._failed_attempts[ip_address] = curr_fails

        logger.warning(
            "Face login failed (attempt %d/2) for IP %s. Reason: %s",
            curr_fails,
            ip_address,
            reason,
        )

        # 1. Always log failed attempt with captured face image in usage_logs
        try:
            self.usage_logs.create_log(
                username="Unregistered / Unknown Face",
                email="n/a (failed scan)",
                action="FAILED_FACE_LOGIN",
                ip_address=ip_address,
                user_agent=user_agent,
                captured_face_image=image_base64,
            )
        except Exception as log_exc:
            logger.error("Failed to persist failed face scan log: %s", log_exc)

        # 2. On 2nd consecutive failed scan -> Dispatch email alert with captured image to Super Admins
        if curr_fails >= 2:
            logger.warning(
                "Threshold reached (2 consecutive failed face scans for IP %s). Dispatching Super Admin alert...",
                ip_address,
            )
            self._dispatch_super_admin_alert(
                image_base64=image_base64,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            FaceLoginService._failed_attempts[ip_address] = 0

    def _dispatch_super_admin_alert(
        self,
        *,
        image_base64: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        super_admins = self.users.find_super_admins()
        if not super_admins:
            logger.warning("No SUPER_ADMIN users found in database to receive security alert.")
            return

        if not self.email_sender:
            logger.warning("Email sender not available to dispatch security alert.")
            return

        # Fetch warning template from app_settings collection
        template_info = (
            self.app_settings.get_email_template_by_key("warning")
            if self.app_settings
            else {
                "subject": "⚠️ Security Alert — 2 Failed Face Scans Detected",
                "body": "# Security Warning Alert\n\nWe detected 2 consecutive failed facial recognition attempts from IP `{{ip_address}}` on {{timestamp}}.",
            }
        )

        subject = template_info.get("subject") or "⚠️ Security Alert — Multiple Failed Login Scans"
        body_markdown = template_info.get("body") or ""

        now_str = format_ist_display(datetime.now(timezone.utc)) or "N/A"
        context = {
            "name": "Super Admin",
            "email": "superadmin@predator.console",
            "ip_address": ip_address,
            "timestamp": now_str,
        }

        html_rendered = render_markdown_to_html(body_markdown, context)

        for sa in super_admins:
            sa_email = sa.get("email")
            if not sa_email:
                continue
            try:
                self.email_sender.send_html_with_image_attachment(
                    to_email=sa_email,
                    subject=subject,
                    html_body=html_rendered,
                    image_base64=image_base64,
                    filename="unregistered_face_capture.jpg",
                )
                logger.info("Security alert with face snapshot sent to Super Admin: %s", sa_email)
            except Exception as exc:
                logger.error("Failed to send security alert to Super Admin %s: %s", sa_email, exc)

        try:
            self.usage_logs.create_log(
                username="PREDATOR Security System",
                email="system@predator.console",
                action="SECURITY_ALERT_SENT",
                ip_address=ip_address,
                user_agent=user_agent,
                captured_face_image=image_base64,
            )
        except Exception:
            pass
