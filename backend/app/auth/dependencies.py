from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.dependencies import get_db

from . import models, service, utils
from .exceptions import (
    InvalidTokenException,
)

# Fix the tokenUrl - it should be relative to the docs page
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",  # Remove the leading slash
    scheme_name="Bearer",
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],  # Use Annotated consistently
) -> models.User:
    """Get current authenticated user from JWT token."""
    try:
        email = utils.extract_email_from_token(token)
    except InvalidTokenException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = service.auth_service.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    """Get current active user."""
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[models.User, Depends(get_current_user)]
CurrentActiveUser = Annotated[models.User, Depends(get_current_active_user)]
