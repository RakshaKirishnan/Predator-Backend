"""Usage logs persistence for signups, logins, and logouts."""

from __future__ import annotations

import uuid
import logging
import urllib.request
import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.mongo import MongoDB
from app.core.exceptions import StorageError

from app.core.timezone import to_ist

logger = logging.getLogger(__name__)


def get_ip_location(ip: str) -> str:
    """Resolve location for an IP address. Uses loopback for local IPs."""
    ip = (ip or "").strip()
    if not ip or ip in {"127.0.0.1", "::1", "localhost"}:
        return "Local Host"
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
        return "Internal Network"

    try:
        # Query free ip-api service with 2 seconds timeout
        url = f"http://ip-api.com/json/{ip}"
        with urllib.request.urlopen(url, timeout=2.0) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "success":
                city = data.get("city")
                country = data.get("country")
                if city and country:
                    return f"{city}, {country}"
                return country or "Unknown Location"
    except Exception:
        pass
    return "Unknown Location"


class UsageLogRepository:
    def __init__(self, mongo: MongoDB):
        self._col = mongo.usage_logs

    def create_log(
        self,
        *,
        username: str,
        email: str,
        action: str,
        ip_address: str,
        user_agent: str,
        captured_face_image: str | None = None,
    ) -> dict[str, Any]:
        location = get_ip_location(ip_address)
        now = datetime.now(timezone.utc)
        doc = {
            "log_id": str(uuid.uuid4()),
            "username": username.strip() or email,
            "email": email.strip().lower(),
            "action": action.strip().upper(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "location": location,
            "captured_face_image": captured_face_image,
            "timestamp": now,
        }
        try:
            self._col.insert_one(doc)
        except Exception as exc:
            raise StorageError(f"Failed to save usage log: {exc}") from exc

        out = dict(doc)
        out.pop("_id", None)
        out["timestamp"] = to_ist(now)
        return out

    def list_logs(self, *, page: int = 1, limit: int = 10) -> tuple[list[dict[str, Any]], int]:
        if page < 1:
            page = 1
        skip = (page - 1) * limit
        try:
            total = self._col.count_documents({})
            cursor = self._col.find({}, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
            raw_logs = list(cursor)
            formatted_logs = []
            for item in raw_logs:
                log_item = dict(item)
                log_item["timestamp"] = to_ist(log_item.get("timestamp"))
                formatted_logs.append(log_item)
            return formatted_logs, total
        except Exception as exc:
            raise StorageError(f"Failed to list usage logs: {exc}") from exc
