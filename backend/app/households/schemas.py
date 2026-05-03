import uuid
from datetime import datetime

from pydantic import ConfigDict, Field

from app.auth.constants import UserRole
from app.schemas import AppBaseModel


class HouseholdBase(AppBaseModel):
    """Base schema with shared household fields."""

    name: str = Field(..., min_length=1, max_length=100)


class HouseholdCreate(HouseholdBase):
    """Schema for creating a new household."""


class HouseholdUpdate(AppBaseModel):
    """Schema for partially updating a household."""

    name: str | None = Field(None, min_length=1, max_length=100)


class HouseholdResponse(HouseholdBase):
    """Full household response including DB-generated fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime


class HouseholdMemberResponse(AppBaseModel):
    """User summary returned when listing household members."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    active: bool


class AddMemberRequest(AppBaseModel):
    """Request body for adding a user to a household."""

    user_id: uuid.UUID


class SetActiveHouseholdRequest(AppBaseModel):
    """Request body for switching the caller's active household."""

    household_id: uuid.UUID
