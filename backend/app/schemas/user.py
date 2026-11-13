"""
Pydantic schemas for Phase 7 User Management and Authentication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for student user registration."""
    email: str = Field(..., description="Student email address")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Student full name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean.split("@")[-1] or len(clean) < 5:
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""
    email: str = Field(..., description="Student email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserProfile(BaseModel):
    """Public safe representation of student user."""
    user_id: str
    email: str
    full_name: str
    created_at: str
    is_active: bool = True


class TokenResponse(BaseModel):
    """JWT Bearer token and authenticated user payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserProfile


class UserStatsResponse(BaseModel):
    """Quick summary of student activity and ownership."""
    user_id: str
    total_documents: int
    total_chats: int
    total_resumes: int
    total_mock_interviews: int
    total_aptitude_attempts: int
