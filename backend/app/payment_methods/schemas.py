import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .constants import CurrencyCode, PaymentMethodType


class PaymentMethodBase(BaseModel):
    """Base payment method schema with common fields."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Payment method name"
    )
    method_type: PaymentMethodType = Field(..., description="Type of payment method")
    default_currency: CurrencyCode = Field(
        ..., description="Default currency for this payment method"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate payment method name."""
        name = v.strip()
        if not name:
            raise ValueError("Payment method name cannot be empty")
        return name

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class PaymentMethodCreate(PaymentMethodBase):
    """Payment method creation schema."""


class PaymentMethodUpdate(BaseModel):
    """Payment method update schema."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Payment method name"
    )
    description: str | None = Field(None, max_length=500, description="Description")
    active: bool | None = Field(
        None, description="Whether the payment method is active"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate payment method name."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Payment method name cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class PaymentMethodResponse(PaymentMethodBase):
    """Payment method response schema."""

    id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentMethodSummary(BaseModel):
    """Payment method summary for nested responses."""

    id: uuid.UUID
    name: str
    method_type: PaymentMethodType

    model_config = {"from_attributes": True}
