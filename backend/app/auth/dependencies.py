from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api_tokens.constants import TOKEN_PREFIX as API_TOKEN_PREFIX
from app.api_tokens.service import api_token_service
from app.database import get_db

from . import models, service, utils
from .exceptions import (
    InvalidTokenExceptionError,
)

# Fix the tokenUrl - it should be relative to the docs page
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",  # Remove the leading slash
    scheme_name="Bearer",
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    """Get the current authenticated user from a JWT or access token.

    Bearer tokens come in two shapes: short-lived JWTs issued by
    ``/auth/login``, and long-lived personal access tokens (PATs) the user
    generates. PATs carry a fixed prefix, so they are resolved against the
    ``api_tokens`` table; anything else is treated as a JWT.
    """
    if token.startswith(API_TOKEN_PREFIX):
        user = api_token_service.resolve_token(db, token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    try:
        username = utils.extract_username_from_token(token)
    except InvalidTokenExceptionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = service.auth_service.get_user_by_username(db, username=username)
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


async def get_current_admin_user(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.User:
    """Get current user and assert they have the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[models.User, Depends(get_current_user)]
CurrentActiveUser = Annotated[models.User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[models.User, Depends(get_current_admin_user)]
