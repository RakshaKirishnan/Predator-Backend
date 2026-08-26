"""SMTP email sender (stdlib smtplib)."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.config import FaceAuthConfig
from app.core.exceptions import EmailSendError

logger = logging.getLogger(__name__)


import base64
from email.mime.image import MIMEImage


class SmtpEmailSender:
    def __init__(self, config: FaceAuthConfig):
        self.config = config

    def send_html(self, *, to_email: str, subject: str, html_body: str) -> None:
        if not self.config.smtp_username or not self.config.smtp_password:
            raise EmailSendError(
                "SMTP is not configured. Set FACE_AUTH_SMTP_USERNAME and "
                "FACE_AUTH_SMTP_PASSWORD."
            )

        from_email = self.config.from_email or self.config.smtp_username
        msg = MIMEMultipart()
        msg["From"] = formataddr((self.config.from_alias, from_email))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMTP send failed to=%s", to_email)
            raise EmailSendError(f"Failed to send email: {exc}") from exc

    def send_html_with_image_attachment(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        image_base64: str,
        filename: str = "unregistered_face_capture.jpg",
    ) -> None:
        if not self.config.smtp_username or not self.config.smtp_password:
            raise EmailSendError("SMTP is not configured.")

        from_email = self.config.from_email or self.config.smtp_username
        msg = MIMEMultipart("related")
        msg["From"] = formataddr((self.config.from_alias, from_email))
        msg["To"] = to_email
        msg["Subject"] = subject

        # Clean base64 string
        raw_b64 = image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(raw_b64)

        # Inline HTML preview placeholder replacement
        inline_html = html_body
        if "cid:unregistered_face" not in inline_html:
            inline_html += f'<br><div style="margin-top:1.5rem;text-align:center;"><p style="font-weight:bold;color:#dc2626;">Captured Unregistered Face Snapshot:</p><img src="cid:unregistered_face" style="max-width:320px;border-radius:12px;border:2px solid #ef4444;box-shadow:0 4px 12px rgba(0,0,0,0.15);"/></div>'

        msg.attach(MIMEText(inline_html, "html"))

        # Attach image as inline CID and file attachment
        img_part = MIMEImage(image_bytes, _subtype="jpeg")
        img_part.add_header("Content-ID", "<unregistered_face>")
        img_part.add_header("Content-Disposition", "inline", filename=filename)
        msg.attach(img_part)

        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMTP send with attachment failed to=%s", to_email)
            raise EmailSendError(f"Failed to send email with image attachment: {exc}") from exc

