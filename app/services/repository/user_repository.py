"""User persistence (account + face embedding)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.exceptions import StorageError, UserAlreadyExistsError
from app.db.mongo import MongoDB


class UserRepository:
    def __init__(self, mongo: MongoDB):
        self._col = mongo.users

    def count(self) -> int:
        return int(self._col.count_documents({}))

    def find_by_email(self, email: str) -> Optional[dict[str, Any]]:
        email_l = email.strip().lower()
        return self._col.find_one(
            {"email": email_l, "is_deleted": {"$ne": True}},
            {"_id": 0},
        )

    def list_with_embeddings(self) -> list[dict[str, Any]]:
        cursor = self._col.find(
            {
                "is_deleted": {"$ne": True},
                "face_embedding": {"$exists": True, "$ne": []},
            },
            {"_id": 0},
        )
        return list(cursor)

    def list_all_users(self) -> list[dict[str, Any]]:
        cursor = self._col.find(
            {"is_deleted": {"$ne": True}},
            {"_id": 0, "face_embedding": 0, "descriptor": 0},
        ).sort("created_at", -1)
        return list(cursor)

    def find_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        return self._col.find_one(
            {"user_id": user_id, "is_deleted": {"$ne": True}},
            {"_id": 0},
        )

    def find_super_admins(self) -> list[dict[str, Any]]:
        cursor = self._col.find(
            {"role": "SUPER_ADMIN", "is_deleted": {"$ne": True}},
            {"_id": 0, "face_embedding": 0},
        )
        return list(cursor)


    def update_user(self, user_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        updates["updated_at"] = datetime.now(timezone.utc)
        self._col.update_one(
            {"user_id": user_id, "is_deleted": {"$ne": True}},
            {"$set": updates},
        )
        return self.find_by_id(user_id)

    def create_user(

        self,
        *,
        email: str,
        name: str,
        face_embedding: list[float],
        role: str = "USER",
    ) -> dict[str, Any]:
        email_l = email.strip().lower()
        if self.find_by_email(email_l):
            raise UserAlreadyExistsError("User with this email already exists")

        now = datetime.now(timezone.utc)
        doc = {
            "user_id": str(uuid.uuid4()),
            "email": email_l,
            "name": name.strip(),
            "role": role.strip().upper(),
            "face_embedding": face_embedding,
            "descriptor": face_embedding,
            "face_embedding_dim": len(face_embedding),
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
        try:
            self._col.insert_one(doc)
        except Exception as exc:  # noqa: BLE001
            if "duplicate" in str(exc).lower():
                raise UserAlreadyExistsError(
                    "User with this email already exists"
                ) from exc
            raise StorageError(f"Failed to create user: {exc}") from exc

        doc.pop("_id", None)
        return doc
