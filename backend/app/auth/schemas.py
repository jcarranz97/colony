from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
import uuid


class CurrencyCode(str, Enum):
    USD = "USD"
    MXN = "MXN"


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    email: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_currency: CurrencyCode = CurrencyCode.USD
    locale: str = "en-US"


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_currency: Optional[CurrencyCode] = None
    locale: Optional[str] = None


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserResponse(UserBase):
    id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    password_hash: str
