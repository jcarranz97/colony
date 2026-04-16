from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import schemas, service
from .dependencies import ExpenseTemplateDep
from .exceptions import (
    ExpenseTemplateNotFoundExceptionError,
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
)

router = APIRouter(prefix="/expense-templates", tags=["expense-templates"])

# Dependency alias for database session
DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/health",
    summary="Expense templates health check",
    description="Health check endpoint for expense templates domain",
)
async def expense_templates_health_check() -> dict[str, str]:
    """Expense templates domain health check."""
    return {"status": "healthy", "domain": "expense_templates"}


@router.get(
    "/",
    response_model=list[schemas.ExpenseTemplateResponse],
    summary="Get all expense templates",
    description=(
        "Retrieve all expense templates for the authenticated user "
        "with optional filters"
    ),
)
async def get_expense_templates(
    current_user: CurrentActiveUser,
    db: DatabaseDep,
    active: bool | None = Query(None, description="Filter by active status"),
    category: str | None = Query(None, description="Filter by category"),
    currency: str | None = Query(None, description="Filter by currency"),
) -> list[schemas.ExpenseTemplateResponse]:
    """Get all expense templates for the authenticated user."""
    templates = service.expense_template_service.get_expense_templates(
        db, str(current_user.id), active=active, category=category, currency=currency
    )
    return [schemas.ExpenseTemplateResponse.model_validate(t) for t in templates]


@router.post(
    "/",
    response_model=schemas.ExpenseTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense template",
    description="Create a new expense template for the authenticated user",
)
async def create_expense_template(
    data: schemas.ExpenseTemplateCreate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.ExpenseTemplateResponse:
    """Create a new expense template."""
    try:
        template = service.expense_template_service.create_expense_template(
            db, data, str(current_user.id)
        )
        return schemas.ExpenseTemplateResponse.model_validate(template)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get(
    "/{expense_template_id}",
    response_model=schemas.ExpenseTemplateResponse,
    summary="Get an expense template",
    description="Retrieve a specific expense template by ID",
)
async def get_expense_template(
    template: ExpenseTemplateDep,
) -> schemas.ExpenseTemplateResponse:
    """Get a specific expense template by ID."""
    return schemas.ExpenseTemplateResponse.model_validate(template)


@router.put(
    "/{expense_template_id}",
    response_model=schemas.ExpenseTemplateResponse,
    summary="Update an expense template",
    description="Update an existing expense template",
)
async def update_expense_template(
    data: schemas.ExpenseTemplateUpdate,
    template: ExpenseTemplateDep,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.ExpenseTemplateResponse:
    """Update an existing expense template."""
    try:
        updated = service.expense_template_service.update_expense_template(
            db, template, data, str(current_user.id)
        )
        return schemas.ExpenseTemplateResponse.model_validate(updated)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except InvalidRecurrenceConfigExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{expense_template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense template",
    description="Soft delete an expense template (deactivate)",
)
async def delete_expense_template(
    template: ExpenseTemplateDep,
    db: DatabaseDep,
) -> None:
    """Soft delete an expense template."""
    try:
        service.expense_template_service.delete_expense_template(db, template)
    except ExpenseTemplateNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
