from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.database import get_db

from . import models, service
from .exceptions import ApiTokenNotFoundExceptionError


async def get_api_token_by_id(
    token_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> models.ApiToken:
    """Resolve an API token by ID, verifying it belongs to the current user."""
    token = service.api_token_service.get_token_by_id(db, token_id, current_user.id)
    if token is None:
        raise ApiTokenNotFoundExceptionError(str(token_id))
    return token


ApiTokenDep = Annotated[models.ApiToken, Depends(get_api_token_by_id)]
