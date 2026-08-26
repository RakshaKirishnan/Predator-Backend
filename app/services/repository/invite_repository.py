"""Invitation token persistence."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.exceptions import InviteExpiredError, InviteInvalidError, StorageError
from app.db.mongo import MongoDB


from app.core.timezone import to_ist


class InviteRepository:
    def __init__(self, mongo: MongoDB, *, ttl_hours: int = 48):
        self._col = mongo.invites
        self.ttl_hours = ttl_hours

    def create_invite(
        self,
        *,
        email: str,
        name: str,
        role: str = "USER",
        invited_by: Optional[str] = None,
    ) -> dict[str, Any]:
        email_l = email.strip().lower()
        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)

        # Invalidate previous unused invites for this email
        self._col.update_many(
            {"email": email_l, "used_at": None, "revoked_at": None},
            {"$set": {"revoked_at": now}},
        )

        doc = {
            "token": token,
            "email": email_l,
            "name": (name or "").strip() or email_l,
            "role": role.strip().upper(),
            "invited_by": invited_by,
            "created_at": now,
            "expires_at": now + timedelta(hours=self.ttl_hours),
            "used_at": None,
            "revoked_at": None,
        }
        try:
            self._col.insert_one(doc)
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"Failed to create invite: {exc}") from exc

        out = dict(doc)
        out.pop("_id", None)
        out["created_at"] = to_ist(out.get("created_at"))
        out["expires_at"] = to_ist(out.get("expires_at"))
        return out

    def get_valid_invite(self, token: str) -> dict[str, Any]:
        token = (token or "").strip()
        if not token:
            raise InviteInvalidError("Invitation token is required")

        doc = self._col.find_one({"token": token}, {"_id": 0})
        if not doc:
            raise InviteInvalidError("Invalid invitation token")
        if doc.get("revoked_at"):
            raise InviteInvalidError("Invitation has been revoked")
        if doc.get("used_at"):
            raise InviteInvalidError("Invitation has already been used")

        expires_at = doc.get("expires_at")
        if expires_at is not None:
            if getattr(expires_at, "tzinfo", None) is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise InviteExpiredError("Invitation has expired")

        out = dict(doc)
        out["created_at"] = to_ist(out.get("created_at"))
        out["expires_at"] = to_ist(out.get("expires_at"))
        return out

    def mark_used(self, token: str) -> None:
        self._col.update_one(
            {"token": token},
            {"$set": {"used_at": datetime.now(timezone.utc)}},
        )

    def list_all_invites(self) -> list[dict[str, Any]]:
        cursor = self._col.find({}, {"_id": 0}).sort("created_at", -1)
        raw_invites = list(cursor)
        formatted_invites = []
        for inv in raw_invites:
            item = dict(inv)
            item["created_at"] = to_ist(item.get("created_at"))
            item["expires_at"] = to_ist(item.get("expires_at"))
            if item.get("used_at"):
                item["used_at"] = to_ist(item.get("used_at"))
            formatted_invites.append(item)
        return formatted_invites
