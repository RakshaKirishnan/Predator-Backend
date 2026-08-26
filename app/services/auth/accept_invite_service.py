"""POST /auth/accept-invite — validate token + enroll face + issue cookies."""

from __future__ import annotations

from fastapi import Response

from app.core.exceptions import InviteInvalidError
from app.services.auth.face_embedding_service import FaceEmbeddingService
from app.services.auth.token_service import TokenService
from app.services.repository.invite_repository import InviteRepository
from app.services.repository.user_repository import UserRepository


from app.services.repository.usage_log_repository import UsageLogRepository


class AcceptInviteService:
    def __init__(
        self,
        *,
        users: UserRepository,
        invites: InviteRepository,
        face_embeddings: FaceEmbeddingService,
        tokens: TokenService,
        usage_logs: UsageLogRepository,
    ):
        self.users = users
        self.invites = invites
        self.face_embeddings = face_embeddings
        self.tokens = tokens
        self.usage_logs = usage_logs

    def accept_invite(
        self,
        *,
        token: str,
        email: str,
        name: str,
        image_base64: str,
        response: Response,
        ip_address: str = "127.0.0.1",
        user_agent: str = "",
    ) -> dict:
        invite = self.invites.get_valid_invite(token)

        invite_email = str(invite.get("email") or "").strip().lower()
        input_email = email.strip().lower()
        if invite_email != input_email:
            raise InviteInvalidError("Invite email does not match registration email")

        face = self.face_embeddings.from_image_base64(image_base64)
        display_name = (name or "").strip() or invite.get("name") or input_email
        role = str(invite.get("role") or "USER").upper()

        user = self.users.create_user(
            email=input_email,
            name=display_name,
            face_embedding=face.embedding,
            role=role,
        )
        self.invites.mark_used(token)

        tokens_dict = self.tokens.set_auth_cookies(
            response,
            email=user["email"],
            role=user["role"],
            user_id=user["user_id"],
        )

        try:
            self.usage_logs.create_log(
                username=user["name"],
                email=user["email"],
                action="SIGNUP",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            pass  # Non-blocking log persistence

        return {
            "success": True,
            "status_code": 201,
            "message": "Invitation accepted",
            "data": {
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "access_token": tokens_dict.get("access_token"),
            },
        }
