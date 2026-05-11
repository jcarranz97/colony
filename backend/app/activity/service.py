"""Activity log and comments service layer.

This module is imported by other domains to record their mutations
(`activity_service.record(...)`). It must not import any other domain's
service module — domains are isolated.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth.models import User

from . import models
from .constants import (
    COMMENTABLE_ENTITY_TYPES,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ActivityAction,
    EntityType,
)
from .exceptions import (
    CommentDeleteForbiddenExceptionError,
    CommentNotAuthorExceptionError,
    CommentNotFoundExceptionError,
    InvalidEntityTypeExceptionError,
)

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for recording and querying the activity log."""

    @staticmethod
    def record(
        db: Session,
        *,
        household_id: uuid.UUID,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        action: ActivityAction,
        cycle_id: uuid.UUID | None = None,
        changes: dict[str, Any] | None = None,
    ) -> models.ActivityLog:
        """Write an activity row.

        Flushes but does not commit — the caller (typically another
        domain's service method) controls the transaction so the
        recorded event is atomic with the underlying mutation.
        """
        entry = models.ActivityLog(
            household_id=household_id,
            entity_type=entity_type.value,
            entity_id=entity_id,
            cycle_id=cycle_id,
            actor_user_id=actor_user_id,
            action=action.value,
            changes=changes or {},
        )
        db.add(entry)
        db.flush()
        logger.info(
            "Activity recorded",
            extra={
                "activity_id": str(entry.id),
                "entity_type": entity_type.value,
                "entity_id": str(entity_id),
                "action": action.value,
            },
        )
        return entry

    @staticmethod
    def list_for_entity(
        db: Session,
        *,
        household_id: uuid.UUID,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        limit: int = DEFAULT_PAGE_SIZE,
        before: datetime | None = None,
    ) -> list[models.ActivityLog]:
        """Return activity rows for a single entity, newest first."""
        limit = min(limit, MAX_PAGE_SIZE)
        query = db.query(models.ActivityLog).filter(
            models.ActivityLog.household_id == household_id,
            models.ActivityLog.entity_type == entity_type.value,
            models.ActivityLog.entity_id == entity_id,
        )
        if before is not None:
            query = query.filter(models.ActivityLog.created_at < before)
        return query.order_by(desc(models.ActivityLog.created_at)).limit(limit).all()

    @staticmethod
    def list_for_cycle(
        db: Session,
        *,
        household_id: uuid.UUID,
        cycle_id: uuid.UUID,
        limit: int = DEFAULT_PAGE_SIZE,
        before: datetime | None = None,
    ) -> list[models.ActivityLog]:
        """Return activity for a cycle (events on cycle + its expenses/incomes)."""
        limit = min(limit, MAX_PAGE_SIZE)
        query = db.query(models.ActivityLog).filter(
            models.ActivityLog.household_id == household_id,
            models.ActivityLog.cycle_id == cycle_id,
        )
        if before is not None:
            query = query.filter(models.ActivityLog.created_at < before)
        return query.order_by(desc(models.ActivityLog.created_at)).limit(limit).all()


class CommentService:
    """Service for creating, editing, deleting, and listing comments."""

    @staticmethod
    def create(
        db: Session,
        *,
        household_id: uuid.UUID,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        body: str,
        actor: User,
        cycle_id: uuid.UUID | None = None,
    ) -> models.Comment:
        """Create a new comment and record a ``commented`` activity event."""
        if entity_type not in COMMENTABLE_ENTITY_TYPES:
            raise InvalidEntityTypeExceptionError(entity_type.value)

        logger.info(
            "Creating comment",
            extra={
                "entity_type": entity_type.value,
                "entity_id": str(entity_id),
                "author_user_id": str(actor.id),
            },
        )

        comment = models.Comment(
            household_id=household_id,
            entity_type=entity_type.value,
            entity_id=entity_id,
            cycle_id=cycle_id,
            author_user_id=actor.id,
            body=body,
        )
        db.add(comment)
        db.flush()

        ActivityService.record(
            db,
            household_id=household_id,
            entity_type=entity_type,
            entity_id=entity_id,
            cycle_id=cycle_id,
            actor_user_id=actor.id,
            action=ActivityAction.COMMENTED,
            changes={"comment_id": str(comment.id)},
        )

        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def update(
        db: Session,
        *,
        comment: models.Comment,
        body: str,
        actor: User,
    ) -> models.Comment:
        """Update a comment body. Author-only."""
        if comment.author_user_id != actor.id:
            raise CommentNotAuthorExceptionError(str(comment.id))

        comment.body = body
        comment.edited_at = datetime.now(UTC)
        db.flush()

        ActivityService.record(
            db,
            household_id=comment.household_id,
            entity_type=EntityType(comment.entity_type),
            entity_id=comment.entity_id,
            cycle_id=comment.cycle_id,
            actor_user_id=actor.id,
            action=ActivityAction.COMMENT_EDITED,
            changes={"comment_id": str(comment.id)},
        )

        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def soft_delete(
        db: Session,
        *,
        comment: models.Comment,
        actor: User,
    ) -> None:
        """Soft-delete a comment. Author OR admin."""
        is_author = comment.author_user_id == actor.id
        is_admin = actor.role == "admin"
        if not (is_author or is_admin):
            raise CommentDeleteForbiddenExceptionError(str(comment.id))

        comment.active = False
        db.flush()

        ActivityService.record(
            db,
            household_id=comment.household_id,
            entity_type=EntityType(comment.entity_type),
            entity_id=comment.entity_id,
            cycle_id=comment.cycle_id,
            actor_user_id=actor.id,
            action=ActivityAction.COMMENT_DELETED,
            changes={"comment_id": str(comment.id)},
        )

        db.commit()

    @staticmethod
    def get_by_id(
        db: Session,
        comment_id: uuid.UUID,
        household_id: uuid.UUID,
    ) -> models.Comment | None:
        """Look up an active comment scoped to a household."""
        return (
            db.query(models.Comment)
            .filter(
                models.Comment.id == comment_id,
                models.Comment.household_id == household_id,
                models.Comment.active.is_(True),
            )
            .first()
        )

    @staticmethod
    def require_by_id(
        db: Session,
        comment_id: uuid.UUID,
        household_id: uuid.UUID,
    ) -> models.Comment:
        """Look up an active comment; raise if missing."""
        comment = CommentService.get_by_id(db, comment_id, household_id)
        if comment is None:
            raise CommentNotFoundExceptionError(str(comment_id))
        return comment

    @staticmethod
    def list_for_entity(
        db: Session,
        *,
        household_id: uuid.UUID,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        limit: int = DEFAULT_PAGE_SIZE,
        before: datetime | None = None,
    ) -> list[models.Comment]:
        """Return active comments for a single entity, newest first."""
        limit = min(limit, MAX_PAGE_SIZE)
        query = db.query(models.Comment).filter(
            models.Comment.household_id == household_id,
            models.Comment.entity_type == entity_type.value,
            models.Comment.entity_id == entity_id,
            models.Comment.active.is_(True),
        )
        if before is not None:
            query = query.filter(models.Comment.created_at < before)
        return query.order_by(desc(models.Comment.created_at)).limit(limit).all()

    @staticmethod
    def list_for_cycle(
        db: Session,
        *,
        household_id: uuid.UUID,
        cycle_id: uuid.UUID,
        limit: int = DEFAULT_PAGE_SIZE,
        before: datetime | None = None,
    ) -> list[models.Comment]:
        """Return all comments inside a cycle (cycle + items), newest first."""
        limit = min(limit, MAX_PAGE_SIZE)
        query = db.query(models.Comment).filter(
            models.Comment.household_id == household_id,
            models.Comment.cycle_id == cycle_id,
            models.Comment.active.is_(True),
        )
        if before is not None:
            query = query.filter(models.Comment.created_at < before)
        return query.order_by(desc(models.Comment.created_at)).limit(limit).all()


activity_service = ActivityService()
comment_service = CommentService()
