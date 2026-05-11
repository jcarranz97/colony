from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    MAX_COMMENT_BODY_LENGTH,
    ActivityAction,
    EntityType,
)


class ActorSummary(BaseModel):
    """Lightweight user info embedded in activity and comment responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


class ActivityResponse(BaseModel):
    """One row in an activity feed."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: EntityType
    entity_id: UUID
    cycle_id: UUID | None
    actor: ActorSummary
    action: ActivityAction
    changes: dict[str, Any]
    created_at: datetime


class CommentCreate(BaseModel):
    """Payload for creating a new comment."""

    entity_type: EntityType
    entity_id: UUID
    body: str = Field(..., min_length=1, max_length=MAX_COMMENT_BODY_LENGTH)

    @field_validator("body")
    @classmethod
    def _strip_and_require_nonempty(cls, value: str) -> str:
        """Strip surrounding whitespace; reject all-whitespace bodies."""
        stripped = value.strip()
        if not stripped:
            msg = "Comment body cannot be empty"
            raise ValueError(msg)
        return stripped


class CommentUpdate(BaseModel):
    """Payload for editing a comment body."""

    body: str = Field(..., min_length=1, max_length=MAX_COMMENT_BODY_LENGTH)

    @field_validator("body")
    @classmethod
    def _strip_and_require_nonempty(cls, value: str) -> str:
        """Strip surrounding whitespace; reject all-whitespace bodies."""
        stripped = value.strip()
        if not stripped:
            msg = "Comment body cannot be empty"
            raise ValueError(msg)
        return stripped


class CommentResponse(BaseModel):
    """A single comment as returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: EntityType
    entity_id: UUID
    cycle_id: UUID | None
    author: ActorSummary
    body: str
    edited_at: datetime | None
    created_at: datetime
    updated_at: datetime
