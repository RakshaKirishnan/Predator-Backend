"""POST /auth/signup — create account + enroll face + issue cookies."""

from __future__ import annotations

from fastapi import Response

from app.services.auth.face_embedding_service import FaceEmbeddingService
from app.services.auth.token_service import TokenService
from app.services.repository.user_repository import UserRepository


from app.services.repository.usage_log_repository import UsageLogRepository


class SignupService:
    def __init__(
        self,
        *,
        users: UserRepository,
        face_embeddings: FaceEmbeddingService,
        tokens: TokenService,
        usage_logs: UsageLogRepository,
    ):
        self.users = users
        self.face_embeddings = face_embeddings
        self.tokens = tokens
        self.usage_logs = usage_logs

    def signup(
        self,
        *,
        email: str,
        name: str,
        image_base64: str,
        response: Response,
        ip_address: str = "127.0.0.1",
        user_agent: str = "",
    ) -> dict:
        face = self.face_embeddings.from_image_base64(image_base64)

        # First user becomes SUPER_ADMIN so they can send invites.
        role = "SUPER_ADMIN" if self.users.count() == 0 else "USER"

        user = self.users.create_user(
            email=email,
            name=name,
            face_embedding=face.embedding,
            role=role,
        )

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
            "message": "Signup successful",
            "data": {
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "access_token": tokens_dict.get("access_token"),
            },
        }
