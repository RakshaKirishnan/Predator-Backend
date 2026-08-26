"""Centralized Timezone Conversion Utilities (UTC to IST)."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

# Indian Standard Time (UTC + 5:30)
IST_TZ = timezone(timedelta(hours=5, minutes=30))


def to_ist(dt: datetime | str | None) -> str | None:
    """
    Convert a UTC datetime or ISO timestamp string to an IST ISO 8601 string.
    Example output: '2026-08-26T13:47:00+05:30'
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        dt_str = dt.strip()
        if not dt_str:
            return None
        try:
            # Parse ISO string
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
            parsed_dt = datetime.fromisoformat(dt_str)
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            ist_dt = parsed_dt.astimezone(IST_TZ)
            return ist_dt.isoformat()
        except ValueError:
            return dt

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(IST_TZ)
        return ist_dt.isoformat()

    return str(dt)


def format_ist_display(dt: datetime | str | None) -> str | None:
    """
    Format a UTC datetime or ISO string as human-readable IST string.
    Example output: '2026-08-26 19:17:00 IST'
    """
    if dt is None:
        return None

    ist_str = to_ist(dt)
    if not ist_str:
        return None

    try:
        parsed = datetime.fromisoformat(ist_str)
        return parsed.strftime("%Y-%m-%d %H:%M:%S IST")
    except ValueError:
        return str(dt)


def convert_dict_timestamps_to_ist(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Convert specified datetime keys in a dictionary to IST ISO string."""
    out = dict(data)
    for field in fields:
        if field in out and out[field] is not None:
            out[field] = to_ist(out[field])
    return out
