"""FastAPI dependencies for the activity / comments domain.

Includes a polymorphic entity resolver that verifies an
``(entity_type, entity_id)`` pair belongs to the active household and
returns the associated cycle id (if any) so it can be denormalized onto
comment / activity rows.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app.cycles.models import Cycle, CycleExpense, CycleIncome
from app.database import get_db
from app.households.dependencies import CurrentActiveHousehold
from app.households.models import Household
from app.payment_methods.models import PaymentMethod
from app.recurrent_expenses.models import RecurrentExpense
from app.recurrent_incomes.models import RecurrentIncome

from . import models
from .constants import EntityType
from .exceptions import (
    CommentNotFoundExceptionError,
    InvalidEntityReferenceExceptionError,
)
from .service import comment_service


def resolve_entity_cycle_id(  # noqa: C901 - one branch per entity type
    db: Session,
    household: Household,
    entity_type: EntityType,
    entity_id: uuid.UUID,
) -> uuid.UUID | None:
    """Verify (entity_type, entity_id) belongs to household; return cycle id.

    Returns the cycle id for cycle-scoped entities (cycle itself, cycle
    expenses, cycle incomes) so it can be denormalized onto the activity /
    comment row. Returns ``None`` for entities not tied to a cycle.

    Raises :class:`InvalidEntityReferenceExceptionError` if the entity
    doesn't exist within the active household.
    """
    if entity_type is EntityType.PAYMENT_METHOD:
        exists = (
            db.query(PaymentMethod.id)
            .filter(
                PaymentMethod.id == entity_id,
                PaymentMethod.household_id == household.id,
            )
            .first()
        )
        if exists is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return None

    if entity_type is EntityType.RECURRENT_EXPENSE:
        exists = (
            db.query(RecurrentExpense.id)
            .filter(
                RecurrentExpense.id == entity_id,
                RecurrentExpense.household_id == household.id,
            )
            .first()
        )
        if exists is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return None

    if entity_type is EntityType.RECURRENT_INCOME:
        exists = (
            db.query(RecurrentIncome.id)
            .filter(
                RecurrentIncome.id == entity_id,
                RecurrentIncome.household_id == household.id,
            )
            .first()
        )
        if exists is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return None

    if entity_type is EntityType.CYCLE:
        exists = (
            db.query(Cycle.id)
            .filter(Cycle.id == entity_id, Cycle.household_id == household.id)
            .first()
        )
        if exists is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return entity_id

    if entity_type is EntityType.CYCLE_EXPENSE:
        row = (
            db.query(CycleExpense.cycle_id)
            .join(Cycle, CycleExpense.cycle_id == Cycle.id)
            .filter(
                CycleExpense.id == entity_id,
                Cycle.household_id == household.id,
            )
            .first()
        )
        if row is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return row[0]

    if entity_type is EntityType.CYCLE_INCOME:
        row = (
            db.query(CycleIncome.cycle_id)
            .join(Cycle, CycleIncome.cycle_id == Cycle.id)
            .filter(
                CycleIncome.id == entity_id,
                Cycle.household_id == household.id,
            )
            .first()
        )
        if row is None:
            raise InvalidEntityReferenceExceptionError(
                entity_type.value, str(entity_id)
            )
        return row[0]

    raise InvalidEntityReferenceExceptionError(entity_type.value, str(entity_id))


async def get_comment_by_id(
    comment_id: Annotated[uuid.UUID, Path()],
    current_household: CurrentActiveHousehold,
    db: Annotated[Session, Depends(get_db)],
) -> models.Comment:
    """Resolve a comment by GUID inside the active household."""
    comment = comment_service.get_by_id(db, comment_id, current_household.id)
    if comment is None:
        raise CommentNotFoundExceptionError(str(comment_id))
    return comment


CommentDep = Annotated[models.Comment, Depends(get_comment_by_id)]
