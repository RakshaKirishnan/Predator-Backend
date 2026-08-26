"""Service for computing dashboard card statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.repository.invite_repository import InviteRepository
from app.services.repository.user_repository import UserRepository


class DashboardCardsService:
    def __init__(
        self,
        *,
        users: UserRepository,
        invites: InviteRepository,
    ):
        self.users = users
        self.invites = invites

    def get_cards_stats(self) -> dict[str, Any]:
        """Aggregate stats for the 4 diagnostic cards on the dashboard."""
        now = datetime.now(timezone.utc)

        users_count = self.users.count()
        invites_col = self.invites._col

        total_invites = invites_col.count_documents({})
        accepted_invites = invites_col.count_documents({"used_at": {"$ne": None}})
        pending_invites = invites_col.count_documents({
            "used_at": None,
            "revoked_at": None,
            "expires_at": {"$gt": now},
        })

        return {
            "users": users_count,
            "pending_invites": pending_invites,
            "accepted_invites": accepted_invites,
            "total_invites": total_invites,
        }
