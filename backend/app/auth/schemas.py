import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas import AppBaseModel

from .constants import UserRole


class CurrencyCode(str, Enum):
    """Supported currency codes."""

    USD = "USD"
    MXN = "MXN"


# Token schemas
class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """JWT token payload data."""

    username: str | None = None


# User schemas
class UserBase(AppBaseModel):
    """Base user model with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    first_name: str | None = None
    last_name: str | None = None
    preferred_currency: CurrencyCode = CurrencyCode.USD
    locale: str = "en-US"
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """User creation schema with password."""

    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserUpdate(AppBaseModel):
    """User update schema for modifying own profile (no role change)."""

    first_name: str | None = None
    last_name: str | None = None
    preferred_currency: CurrencyCode | None = None
    locale: str | None = None


class UserAdminUpdate(AppBaseModel):
    """Admin-only update schema; allows changing role and active status."""

    first_name: str | None = None
    last_name: str | None = None
    preferred_currency: CurrencyCode | None = None
    locale: str | None = None
    role: UserRole | None = None
    active: bool | None = None


class UserUpdatePassword(AppBaseModel):
    """Schema for updating user password."""

    current_password: str
    new_password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserResponse(UserBase):
    """User response schema for API responses."""

    id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration for ORM compatibility."""

        from_attributes = True


class UserInDB(UserResponse):
    """User schema including password hash for internal use."""

    password_hash: str
