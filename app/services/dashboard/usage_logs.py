"""Service for retrieving and managing usage logs."""

from __future__ import annotations

from typing import Any

from app.services.repository.usage_log_repository import UsageLogRepository


class UsageLogsService:
    def __init__(
        self,
        *,
        usage_logs: UsageLogRepository,
    ):
        self.usage_logs = usage_logs

    def get_logs(self, *, page: int = 1, limit: int = 10) -> dict[str, Any]:
        """Retrieve paginated usage logs."""
        logs, total = self.usage_logs.list_logs(page=page, limit=limit)
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "limit": limit,
        }

    def record_log(
        self,
        *,
        username: str,
        email: str,
        action: str,
        ip_address: str,
        user_agent: str,
    ) -> dict[str, Any]:
        """Record a security audit log event."""
        return self.usage_logs.create_log(
            username=username,
            email=email,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
        )
