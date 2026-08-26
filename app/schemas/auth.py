"""Auth request schemas — clients send face images, never embeddings."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=120)
    image_base64: str = Field(..., min_length=32, description="Face capture as data URL or raw base64")


class FaceLoginRequest(BaseModel):
    image_base64: str = Field(..., min_length=32)


class InviteRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=120)
    role: Literal["USER", "ADMIN", "SUPER_ADMIN"] = "USER"


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., min_length=16)
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=120)
    image_base64: str = Field(..., min_length=32)
