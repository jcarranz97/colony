import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from app.schemas import AppBaseModel

from .constants import MAX_TOKEN_NAME_LENGTH


class ApiTokenCreate(AppBaseModel):
    """Request body for creating a new personal access token."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TOKEN_NAME_LENGTH,
        description="A label that identifies where the token is used.",
    )
    expires_at: datetime | None = Field(
        None,
        description="Optional expiry. When omitted, the token never expires.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate the token name is not blank."""
        name = v.strip()
        if not name:
            raise ValueError("Token name cannot be empty")
        return name


class ApiTokenResponse(AppBaseModel):
    """API token metadata — never includes the secret."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    prefix: str
    last_used_at: datetime | None
    expires_at: datetime | None
    active: bool
    created_at: datetime
    updated_at: datetime


class ApiTokenCreatedResponse(ApiTokenResponse):
    """API token response returned once at creation, including the secret."""

    token: str = Field(
        ...,
        description="The plaintext token. Shown only once — store it now.",
    )
