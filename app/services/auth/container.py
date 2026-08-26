"""Wire auth services once at startup (Sameer-style app.state services)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import FaceAuthConfig
from app.db.mongo import MongoDB
from app.services.auth.accept_invite_service import AcceptInviteService
from app.services.auth.face_embedding_service import FaceEmbeddingService
from app.services.auth.face_login_service import FaceLoginService
from app.services.auth.invite_service import InviteService
from app.services.auth.signup_service import SignupService
from app.services.auth.token_service import TokenService
from app.services.email.smtp_sender import SmtpEmailSender
from app.services.engine.insightface_engine import InsightFaceEngine
from app.services.repository.app_settings_repository import AppSettingsRepository
from app.services.repository.invite_repository import InviteRepository
from app.services.repository.user_repository import UserRepository
from app.services.repository.usage_log_repository import UsageLogRepository
from app.services.dashboard.dashboard_cards import DashboardCardsService
from app.services.dashboard.usage_logs import UsageLogsService
from app.services.dashboard.members_service import MembersService


@dataclass
class AuthServices:
    users: UserRepository
    invites: InviteRepository
    usage_logs: UsageLogRepository
    app_settings: AppSettingsRepository
    tokens: TokenService
    signup: SignupService
    face_login: FaceLoginService
    invite: InviteService
    accept_invite: AcceptInviteService
    dashboard_cards: DashboardCardsService
    usage_logs_service: UsageLogsService
    members_service: MembersService


def build_auth_services(
    *,
    config: FaceAuthConfig,
    mongo: MongoDB,
    engine: InsightFaceEngine,
) -> AuthServices:
    users = UserRepository(mongo)
    invites = InviteRepository(mongo, ttl_hours=config.invite_ttl_hours)
    usage_logs = UsageLogRepository(mongo)
    app_settings = AppSettingsRepository(mongo)
    tokens = TokenService(config)
    face_embeddings = FaceEmbeddingService(engine)
    email_sender = SmtpEmailSender(config)

    dashboard_cards = DashboardCardsService(users=users, invites=invites)
    usage_logs_service = UsageLogsService(usage_logs=usage_logs)
    members_service = MembersService(users=users)

    return AuthServices(
        users=users,
        invites=invites,
        usage_logs=usage_logs,
        app_settings=app_settings,
        tokens=tokens,
        signup=SignupService(
            users=users,
            face_embeddings=face_embeddings,
            tokens=tokens,
            usage_logs=usage_logs,
        ),
        face_login=FaceLoginService(
            users=users,
            face_embeddings=face_embeddings,
            tokens=tokens,
            match_threshold=config.match_threshold,
            usage_logs=usage_logs,
            app_settings=app_settings,
            email_sender=email_sender,
        ),

        invite=InviteService(
            config=config,
            users=users,
            invites=invites,
            app_settings=app_settings,
            email_sender=email_sender,
        ),
        accept_invite=AcceptInviteService(
            users=users,
            invites=invites,
            face_embeddings=face_embeddings,
            tokens=tokens,
            usage_logs=usage_logs,
        ),
        dashboard_cards=dashboard_cards,
        usage_logs_service=usage_logs_service,
        members_service=members_service,
    )

