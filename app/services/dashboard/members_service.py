"""Members management service layer."""

from __future__ import annotations

from app.services.repository.user_repository import UserRepository
from app.core.timezone import to_ist


class MembersService:
    def __init__(self, users: UserRepository):
        self.users = users

    def get_members(self) -> dict:
        users = self.users.list_all_users()
        members = []
        for u in users:
            created_at_ist = to_ist(u.get("created_at"))

            members.append({
                "user_id": str(u.get("user_id", "")),
                "email": str(u.get("email", "")),
                "name": str(u.get("name") or u.get("email", "")),
                "role": str(u.get("role", "USER")),
                "status": "Active",
                "created_at": str(created_at_ist or ""),
            })
        return {
            "members": members,
            "total": len(members),
        }

    def update_member(
        self,
        *,
        user_id: str,
        name: str | None = None,
        email: str | None = None,
        role: str | None = None,
    ) -> dict:
        user = self.users.find_by_id(user_id)
        if not user:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(f"Member with ID '{user_id}' not found")

        updates: dict[str, Any] = {}
        if name is not None and name.strip():
            updates["name"] = name.strip()

        if email is not None and email.strip():
            email_l = email.strip().lower()
            if email_l != user.get("email"):
                existing = self.users.find_by_email(email_l)
                if existing and existing.get("user_id") != user_id:
                    from app.core.exceptions import UserAlreadyExistsError
                    raise UserAlreadyExistsError(f"Email '{email_l}' is already in use by another account")
                updates["email"] = email_l

        if role is not None and role.strip():
            role_u = role.strip().upper()
            if role_u not in {"USER", "ADMIN", "SUPER_ADMIN"}:
                from app.core.exceptions import ValidationError
                raise ValidationError("Role must be one of USER, ADMIN, or SUPER_ADMIN")
            updates["role"] = role_u

        if not updates:
            created_at_ist = to_ist(user.get("created_at"))
            return {
                "user_id": str(user.get("user_id", "")),
                "email": str(user.get("email", "")),
                "name": str(user.get("name") or user.get("email", "")),
                "role": str(user.get("role", "USER")),
                "status": "Active",
                "created_at": str(created_at_ist or ""),
            }

        updated_user = self.users.update_user(user_id, updates)
        if not updated_user:
            from app.core.exceptions import StorageError
            raise StorageError("Failed to update user record")

        created_at_ist = to_ist(updated_user.get("created_at"))

        return {
            "user_id": str(updated_user.get("user_id", "")),
            "email": str(updated_user.get("email", "")),
            "name": str(updated_user.get("name") or updated_user.get("email", "")),
            "role": str(updated_user.get("role", "USER")),
            "status": "Active",
            "created_at": str(created_at_ist or ""),
        }

