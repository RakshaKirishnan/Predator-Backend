"""Pydantic schemas for dashboard endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class DashboardCardStats(BaseModel):
    users: int = Field(..., description="Total count of registered user accounts")
    pending_invites: int = Field(..., description="Count of pending invitation tokens")
    accepted_invites: int = Field(..., description="Count of accepted invitation tokens")
    total_invites: int = Field(..., description="Total invitation tokens issued")


class DashboardCardsResponse(BaseModel):
    success: bool = True
    message: str = "Dashboard card metrics retrieved"
    data: DashboardCardStats


class UsageLogItem(BaseModel):
    log_id: str
    username: str
    email: str
    action: str
    ip_address: str
    user_agent: str
    location: str
    captured_face_image: Optional[str] = None
    timestamp: Any



class UsageLogsData(BaseModel):
    logs: list[UsageLogItem]
    total: int
    page: int
    limit: int


class UsageLogsResponse(BaseModel):
    success: bool = True
    message: str = "Usage logs retrieved"
    data: UsageLogsData



