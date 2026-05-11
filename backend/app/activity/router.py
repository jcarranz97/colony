"""HTTP routes for activity feeds and comments.

Two routers live in this module:

- ``router`` (prefix ``/activity``) — read-only activity feeds, filtered
  by entity or by cycle.
- ``comments_router`` (prefix ``/comments``) — CRUD for comments.

They live together so the polymorphic entity-type machinery is shared.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.dependencies import CurrentActiveUser, get_db
from app.households.dependencies import CurrentActiveHousehold

from . import models, schemas, service
from .constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ActivityAction,
    EntityType,
)
from .dependencies import CommentDep, resolve_entity_cycle_id

router = APIRouter(prefix="/activity", tags=["activity"])
comments_router = APIRouter(prefix="/comments", tags=["comments"])

DatabaseDep = Annotated[Session, Depends(get_db)]


def _serialize_actor(db: Session, user_id: uuid.UUID) -> schemas.ActorSummary:
    """Build an ``ActorSummary`` for the given user id."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Soft-deleted users keep their activity but lose their username.
        return schemas.ActorSummary(id=user_id, username="(unknown)")
    return schemas.ActorSummary(id=user.id, username=user.username)


def _activity_to_response(
    db: Session, entry: models.ActivityLog
) -> schemas.ActivityResponse:
    """Hydrate an :class:`ActivityLog` row into its response schema."""
    return schemas.ActivityResponse(
        id=entry.id,
        entity_type=EntityType(entry.entity_type),
        entity_id=entry.entity_id,
        cycle_id=entry.cycle_id,
        actor=_serialize_actor(db, entry.actor_user_id),
        action=ActivityAction(entry.action),
        changes=entry.changes,
        created_at=entry.created_at,
    )


def _comment_to_response(
    db: Session, comment: models.Comment
) -> schemas.CommentResponse:
    """Hydrate a :class:`Comment` row into its response schema."""
    return schemas.CommentResponse(
        id=comment.id,
        entity_type=EntityType(comment.entity_type),
        entity_id=comment.entity_id,
        cycle_id=comment.cycle_id,
        author=_serialize_actor(db, comment.author_user_id),
        body=comment.body,
        edited_at=comment.edited_at,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get(
    "/health",
    summary="Activity health check",
    description="Health check endpoint for the activity domain.",
)
async def activity_health_check() -> dict[str, str]:
    """Activity domain health check."""
    return {"status": "healthy", "domain": "activity"}


@router.get(
    "/",
    response_model=list[schemas.ActivityResponse],
    summary="List activity entries",
    description=(
        "Return an activity feed. Provide either (entity_type + entity_id) "
        "to scope to one entity, or cycle_id to scope to all activity "
        "within a cycle."
    ),
)
async def list_activity(
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
    entity_type: Annotated[
        EntityType | None, Query(description="Polymorphic entity type")
    ] = None,
    entity_id: Annotated[
        uuid.UUID | None, Query(description="Polymorphic entity id")
    ] = None,
    cycle_id: Annotated[
        uuid.UUID | None,
        Query(description="Scope to all events inside this cycle"),
    ] = None,
    before: Annotated[
        datetime | None,
        Query(description="Cursor: return rows with created_at < this"),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Page size")
    ] = DEFAULT_PAGE_SIZE,
) -> list[schemas.ActivityResponse]:
    """List activity entries scoped to one entity or one cycle."""
    if entity_type is not None and entity_id is not None:
        entries = service.activity_service.list_for_entity(
            db,
            household_id=current_household.id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            before=before,
        )
    elif cycle_id is not None:
        entries = service.activity_service.list_for_cycle(
            db,
            household_id=current_household.id,
            cycle_id=cycle_id,
            limit=limit,
            before=before,
        )
    else:
        # No scope provided → empty result rather than household-wide dump
        # (avoid accidentally leaking the full activity log).
        entries = []
    return [_activity_to_response(db, entry) for entry in entries]


@comments_router.get(
    "/health",
    summary="Comments health check",
    description="Health check endpoint for the comments domain.",
)
async def comments_health_check() -> dict[str, str]:
    """Comments domain health check."""
    return {"status": "healthy", "domain": "comments"}


@comments_router.get(
    "/",
    response_model=list[schemas.CommentResponse],
    summary="List comments",
    description=(
        "Return comments scoped to one entity or one cycle. Provide either "
        "(entity_type + entity_id) or cycle_id."
    ),
)
async def list_comments(
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
    entity_type: Annotated[EntityType | None, Query()] = None,
    entity_id: Annotated[uuid.UUID | None, Query()] = None,
    cycle_id: Annotated[uuid.UUID | None, Query()] = None,
    before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> list[schemas.CommentResponse]:
    """List comments for an entity or cycle."""
    if entity_type is not None and entity_id is not None:
        comments = service.comment_service.list_for_entity(
            db,
            household_id=current_household.id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            before=before,
        )
    elif cycle_id is not None:
        comments = service.comment_service.list_for_cycle(
            db,
            household_id=current_household.id,
            cycle_id=cycle_id,
            limit=limit,
            before=before,
        )
    else:
        comments = []
    return [_comment_to_response(db, comment) for comment in comments]


@comments_router.post(
    "/",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
)
async def create_comment(
    payload: schemas.CommentCreate,
    current_household: CurrentActiveHousehold,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.CommentResponse:
    """Create a comment on an entity. Body must be non-empty Markdown."""
    cycle_id = resolve_entity_cycle_id(
        db, current_household, payload.entity_type, payload.entity_id
    )
    comment = service.comment_service.create(
        db,
        household_id=current_household.id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        body=payload.body,
        actor=current_user,
        cycle_id=cycle_id,
    )
    return _comment_to_response(db, comment)


@comments_router.patch(
    "/{comment_id}",
    response_model=schemas.CommentResponse,
    summary="Edit a comment (author only)",
)
async def update_comment(
    payload: schemas.CommentUpdate,
    comment: CommentDep,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.CommentResponse:
    """Edit a comment body. Only the author can edit."""
    updated = service.comment_service.update(
        db, comment=comment, body=payload.body, actor=current_user
    )
    return _comment_to_response(db, updated)


@comments_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment (author or admin)",
)
async def delete_comment(
    comment: CommentDep,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> None:
    """Soft-delete a comment. Author or admin."""
    service.comment_service.soft_delete(db, comment=comment, actor=current_user)
