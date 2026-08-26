"""Runtime configuration for portable face auth."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class FaceAuthConfig:
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8090"))

    # InsightFace
    model_name: str = os.getenv("FACE_AUTH_MODEL", "buffalo_l")
    ctx_id: int = int(os.getenv("FACE_AUTH_CTX_ID", "-1"))
    det_size: tuple[int, int] = (
        int(os.getenv("FACE_AUTH_DET_W", "640")),
        int(os.getenv("FACE_AUTH_DET_H", "640")),
    )
    match_threshold: float = float(os.getenv("FACE_AUTH_MATCH_THRESHOLD", "0.40"))
    max_image_bytes: int = int(
        os.getenv("FACE_AUTH_MAX_IMAGE_BYTES", str(8 * 1024 * 1024))
    )

    # MongoDB
    mongo_uri: str = os.getenv(
        "FACE_AUTH_MONGO_URI",
        os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    )
    mongo_database: str = os.getenv("FACE_AUTH_MONGO_DB", "predator")
    users_collection: str = os.getenv("FACE_AUTH_USERS_COLLECTION", "users")
    invites_collection: str = os.getenv("FACE_AUTH_INVITES_COLLECTION", "invites")
    usage_logs_collection: str = os.getenv("FACE_AUTH_USAGE_LOGS_COLLECTION", "usage_logs")
    app_settings_collection: str = os.getenv("FACE_AUTH_APP_SETTINGS_COLLECTION", "app_settings")
    

    # JWT cookies (Sameer-style)
    secret_key: str = os.getenv(
        "FACE_AUTH_SECRET_KEY", "change-me-access-secret-min-32-chars!!"
    )
    refresh_secret_key: str = os.getenv(
        "FACE_AUTH_REFRESH_SECRET_KEY",
        "change-me-refresh-secret-min-32-chars!",
    )
    jwt_algorithm: str = os.getenv("FACE_AUTH_JWT_ALGORITHM", "HS256")
    access_token_expire_min: int = int(os.getenv("FACE_AUTH_ACCESS_TOKEN_EXPIRE_MIN", "60"))
    refresh_token_expire_hrs: int = int(
        os.getenv("FACE_AUTH_REFRESH_TOKEN_EXPIRE_HRS", "24")
    )
    cookie_samesite: str = os.getenv("FACE_AUTH_COOKIE_SAMESITE", "lax")
    cookie_secure: bool = _env_bool("FACE_AUTH_COOKIE_SECURE", False)
    cookie_domain: str | None = os.getenv("FACE_AUTH_COOKIE_DOMAIN") or None

    # SMTP invite
    smtp_server: str = os.getenv("FACE_AUTH_SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("FACE_AUTH_SMTP_PORT", "587"))
    smtp_username: str = os.getenv("FACE_AUTH_SMTP_USERNAME", "")
    smtp_password: str = os.getenv("FACE_AUTH_SMTP_PASSWORD", "")
    from_email: str = os.getenv("FACE_AUTH_FROM_EMAIL", "")
    from_alias: str = os.getenv("FACE_AUTH_FROM_ALIAS", "Face Auth")
    invite_link_base: str = os.getenv(
        "FACE_AUTH_INVITE_LINK_BASE",
        "http://localhost:3000/auth/accept-invite",
    )
    invite_ttl_hours: int = int(os.getenv("FACE_AUTH_INVITE_TTL_HOURS", "48"))


def get_config() -> FaceAuthConfig:
    return FaceAuthConfig()
