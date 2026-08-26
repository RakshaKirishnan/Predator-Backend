"""JWT access/refresh tokens + Sameer-style cookie helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Response

from app.config import FaceAuthConfig
from app.core.exceptions import UnauthorizedError


class TokenService:
    def __init__(self, config: FaceAuthConfig):
        self.config = config

    def create_access_token(self, *, email: str, role: str, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.config.access_token_expire_min
        )
        payload = {
            "sub": email,
            "role": role,
            "user_id": user_id,
            "type": "access",
            "exp": expire,
        }
        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.jwt_algorithm
        )

    def create_refresh_token(self, *, email: str, role: str, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=self.config.refresh_token_expire_hrs
        )
        payload = {
            "sub": email,
            "role": role,
            "user_id": user_id,
            "type": "refresh",
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self.config.refresh_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

    def set_auth_cookies(
        self,
        response: Response,
        *,
        email: str,
        role: str,
        user_id: str,
    ) -> dict[str, str]:
        access = self.create_access_token(email=email, role=role, user_id=user_id)
        refresh = self.create_refresh_token(email=email, role=role, user_id=user_id)

        common = {
            "httponly": True,
            "samesite": self.config.cookie_samesite,
            "secure": self.config.cookie_secure,
            "path": "/",
        }
        if self.config.cookie_domain:
            common["domain"] = self.config.cookie_domain

        response.set_cookie(
            key="access_token",
            value=access,
            max_age=self.config.access_token_expire_min * 60,
            **common,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            max_age=self.config.refresh_token_expire_hrs * 3600,
            **common,
        )
        return {"access_token": access, "refresh_token": refresh}

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired access token") from exc

        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid access token type")
        return payload

    def require_admin(self, token: Optional[str]) -> dict[str, Any]:
        if not token:
            raise UnauthorizedError("Authentication required")
        payload = self.decode_access_token(token)
        role = str(payload.get("role") or "").upper()
        if role not in {"ADMIN", "SUPER_ADMIN"}:
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError("Admin access required")
        return payload

    def require_super_admin(self, token: Optional[str]) -> dict[str, Any]:
        if not token:
            raise UnauthorizedError("Authentication required")
        payload = self.decode_access_token(token)
        role = str(payload.get("role") or "").upper()
        if role != "SUPER_ADMIN":
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError("Only SUPER_ADMIN can update member details and roles")
        return payload

