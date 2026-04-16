import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import schemas, service
from .dependencies import CycleDep, CycleExpenseDep
from .exceptions import (
    CycleGenerationExceptionError,
    CycleNameExistsExceptionError,
    ExchangeRateNotFoundExceptionError,
    PaymentMethodNotFoundExceptionError,
)

router = APIRouter(prefix="/cycles", tags=["cycles"])

DatabaseDep = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Cycle endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=schemas.CyclesListResponse,
    summary="List cycles",
    description=(
        "Return all cycles for the authenticated user with optional status filter "
        "and pagination."
    ),
)
async def list_cycles(
    current_user: CurrentActiveUser,
    db: DatabaseDep,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by cycle status (draft/active/completed)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> schemas.CyclesListResponse:
    """Return a paginated list of cycles for the authenticated user."""
    cycles, total = service.cycle_service.get_cycles(
        db,
        str(current_user.id),
        status=status_filter,
        page=page,
        per_page=per_page,
    )
    total_pages = math.ceil(total / per_page) if total else 0
    cycle_responses = [schemas.CycleResponse.model_validate(c) for c in cycles]
    return schemas.CyclesListResponse(
        cycles=cycle_responses,
        pagination=schemas.PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            pages=total_pages,
        ),
    )


@router.post(
    "/",
    response_model=schemas.CycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a cycle",
    description=(
        "Create a new expense cycle. Set ``generate_from_templates`` to True to "
        "automatically populate expenses from all active templates."
    ),
)
async def create_cycle(
    data: schemas.CycleCreate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.CycleResponse:
    """Create a new expense cycle."""
    try:
        cycle = service.cycle_service.create_cycle(db, data, str(current_user.id))
        return schemas.CycleResponse.model_validate(cycle)
    except CycleNameExistsExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except CycleGenerationExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ExchangeRateNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{cycle_id}",
    response_model=schemas.CycleResponse,
    summary="Get a cycle",
    description="Retrieve a specific cycle by ID.",
)
async def get_cycle(cycle: CycleDep) -> schemas.CycleResponse:
    """Retrieve a specific cycle."""
    return schemas.CycleResponse.model_validate(cycle)


@router.put(
    "/{cycle_id}",
    response_model=schemas.CycleResponse,
    summary="Update a cycle",
    description="Partially update a cycle's name, income amount, or status.",
)
async def update_cycle(
    data: schemas.CycleUpdate,
    cycle: CycleDep,
    db: DatabaseDep,
) -> schemas.CycleResponse:
    """Partially update a cycle."""
    try:
        updated = service.cycle_service.update_cycle(db, cycle, data)
        return schemas.CycleResponse.model_validate(updated)
    except CycleNameExistsExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{cycle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cycle",
    description="Soft-delete a cycle and all its associated expenses.",
)
async def delete_cycle(cycle: CycleDep, db: DatabaseDep) -> None:
    """Soft-delete a cycle."""
    service.cycle_service.delete_cycle(db, cycle)


@router.get(
    "/{cycle_id}/summary",
    response_model=schemas.CycleSummaryResponse,
    summary="Get cycle summary",
    description=(
        "Return a detailed financial summary for a cycle: totals by category, "
        "by payment method, by currency, and a status count breakdown."
    ),
)
async def get_cycle_summary(cycle: CycleDep) -> schemas.CycleSummaryResponse:
    """Return a detailed financial summary for a cycle."""
    return service.cycle_service.build_cycle_summary(cycle)


# ---------------------------------------------------------------------------
# Cycle expense endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{cycle_id}/expenses",
    response_model=schemas.CycleExpensesListResponse,
    summary="List cycle expenses",
    description="Return all expenses for a cycle with optional filters.",
)
async def list_cycle_expenses(
    cycle_id: str,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by expense status",
    ),
    category: str | None = Query(None, description="Filter by category"),
    currency: str | None = Query(None, description="Filter by currency"),
    payment_method_id: str | None = Query(
        None, description="Filter by payment method UUID"
    ),
) -> schemas.CycleExpensesListResponse:
    """List all expenses for a specific cycle."""
    # Verify the cycle belongs to the authenticated user
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    expenses = service.cycle_expense_service.get_expenses(
        db,
        cycle_id=cycle_id,
        status=status_filter,
        category=category,
        currency=currency,
        payment_method_id=payment_method_id,
    )

    expense_responses = [
        schemas.CycleExpenseResponse.model_validate(e) for e in expenses
    ]
    summary = service.cycle_expense_service.build_expenses_summary(expenses)

    return schemas.CycleExpensesListResponse(
        expenses=expense_responses,
        summary=summary,
    )


@router.post(
    "/{cycle_id}/expenses",
    response_model=schemas.CycleExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a manual expense",
    description="Manually add a new expense to an existing cycle.",
)
async def create_cycle_expense(
    data: schemas.CycleExpenseCreate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
    cycle_id: str,
) -> schemas.CycleExpenseResponse:
    """Add a manual expense to a cycle."""
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    try:
        expense = service.cycle_expense_service.create_expense(
            db, cycle, data, str(current_user.id)
        )
        return schemas.CycleExpenseResponse.model_validate(expense)
    except PaymentMethodNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ExchangeRateNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{cycle_id}/expenses/{expense_id}",
    response_model=schemas.CycleExpenseResponse,
    summary="Get a cycle expense",
    description="Retrieve a specific expense from a cycle.",
)
async def get_cycle_expense(expense: CycleExpenseDep) -> schemas.CycleExpenseResponse:
    """Retrieve a specific cycle expense."""
    return schemas.CycleExpenseResponse.model_validate(expense)


@router.put(
    "/{cycle_id}/expenses/{expense_id}",
    response_model=schemas.CycleExpenseResponse,
    summary="Update a cycle expense",
    description=(
        "Partially update a cycle expense. Setting ``paid=true`` automatically "
        "sets the status to ``paid`` and records a ``paid_at`` timestamp."
    ),
)
async def update_cycle_expense(
    data: schemas.CycleExpenseUpdate,
    expense: CycleExpenseDep,
    cycle_id: str,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.CycleExpenseResponse:
    """Partially update a cycle expense."""
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    try:
        updated = service.cycle_expense_service.update_expense(db, cycle, expense, data)
        return schemas.CycleExpenseResponse.model_validate(updated)
    except ExchangeRateNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{cycle_id}/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cycle expense",
    description="Soft-delete an expense from a cycle.",
)
async def delete_cycle_expense(
    expense: CycleExpenseDep,
    cycle_id: str,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> None:
    """Soft-delete a cycle expense."""
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    service.cycle_expense_service.delete_expense(db, cycle, expense)
