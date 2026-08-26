"""Pydantic schemas for members management."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class MemberItem(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    status: str = "Active"
    created_at: Any


class MembersData(BaseModel):
    members: list[MemberItem]
    total: int


class MembersResponse(BaseModel):
    success: bool = True
    message: str = "Members retrieved"
    data: MembersData


class UpdateMemberRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UpdateMemberResponse(BaseModel):
    success: bool = True
    message: str = "Member updated successfully"
    data: MemberItem

