import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class CurrencyCode(str, Enum):
    """Supported currency codes."""

    USD = "USD"
    MXN = "MXN"


# Token schemas
class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int  # seconds


class TokenData(BaseModel):
    """JWT token payload data."""

    email: str | None = None


# User schemas
class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    preferred_currency: CurrencyCode = CurrencyCode.USD
    locale: str = "en-US"


class UserCreate(UserBase):
    """User creation schema with password."""

    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    """User update schema for modifying user information."""

    first_name: str | None = None
    last_name: str | None = None
    preferred_currency: CurrencyCode | None = None
    locale: str | None = None


class UserUpdatePassword(BaseModel):
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
