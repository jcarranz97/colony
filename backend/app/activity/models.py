import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class ActivityLog(BaseModel):
    """Append-only record of mutations and lifecycle events.

    The log is polymorphic: ``entity_type`` + ``entity_id`` identify the
    target without a foreign-key constraint, which lets the same table
    cover every domain.
    """

    __tablename__ = "activity_log"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Denormalized cycle pointer so "everything that happened in cycle X"
    # is a single indexed query. Null for events on entities not tied to
    # a cycle (payment methods, recurrent templates).
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cycles.id", ondelete="CASCADE"),
        nullable=True,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index(
            "ix_activity_log_household_created",
            "household_id",
            "created_at",
        ),
        Index(
            "ix_activity_log_entity_created",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index(
            "ix_activity_log_cycle_created",
            "cycle_id",
            "created_at",
        ),
        Index(
            "ix_activity_log_actor_created",
            "actor_user_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        """String representation of ActivityLog."""
        return (
            f"<ActivityLog(id={self.id}, action='{self.action}', "
            f"entity={self.entity_type}/{self.entity_id})>"
        )


class Comment(BaseModel):
    """User-authored comment attached polymorphically to any entity."""

    __tablename__ = "comments"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cycles.id", ondelete="CASCADE"),
        nullable=True,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "ix_comments_entity_created",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index(
            "ix_comments_cycle_created",
            "cycle_id",
            "created_at",
        ),
        Index(
            "ix_comments_household_created",
            "household_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Comment."""
        return (
            f"<Comment(id={self.id}, author={self.author_user_id}, "
            f"entity={self.entity_type}/{self.entity_id})>"
        )
