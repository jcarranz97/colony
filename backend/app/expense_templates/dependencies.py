from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import service
from .exceptions import ExpenseTemplateNotFoundExceptionError


async def get_expense_template_by_id(
    expense_template_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.ExpenseTemplate:
    """Resolve and authorize an expense template by path parameter.

    Args:
        expense_template_id: The template UUID from the URL path.
        current_user: The authenticated active user.
        db: Active database session.

    Returns:
        The resolved ExpenseTemplate instance.

    Raises:
        ExpenseTemplateNotFoundExceptionError: If the template does not exist
            or does not belong to the current user.
    """
    template = service.expense_template_service.get_expense_template_by_id(
        db, expense_template_id, str(current_user.id)
    )
    if not template:
        raise ExpenseTemplateNotFoundExceptionError(expense_template_id)
    return template


ExpenseTemplateDep = Annotated[
    service.models.ExpenseTemplate,
    Depends(get_expense_template_by_id),
]
