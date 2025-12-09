from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db

from . import schemas, service
from .dependencies import CurrentActiveUser
from .exceptions import (
    IncorrectPasswordException,
    InvalidCredentialsException,
    UserAlreadyExistsException,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Create dependency aliases to fix B008
DatabaseDep = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: schemas.UserCreate, db: DatabaseDep
) -> schemas.UserResponse:
    """Register a new user."""
    try:
        user = service.auth_service.create_user(db, user_data)
        return schemas.UserResponse.from_orm(user)
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DatabaseDep,
) -> schemas.Token:
    """Login user and return access token."""
    try:
        # Note: OAuth2PasswordRequestForm uses 'username' field, but we use email
        user = service.auth_service.authenticate_user(
            db,
            email=form_data.username,  # Email is passed as username
            password=form_data.password,
        )

        return service.auth_service.create_access_token(user)

    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: CurrentActiveUser,
) -> schemas.UserResponse:
    """Get current user information."""
    return schemas.UserResponse.from_orm(current_user)


@router.put("/me", response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.UserResponse:
    """Update current user information."""
    updated_user = service.auth_service.update_user(db, current_user, user_update)
    return schemas.UserResponse.from_orm(updated_user)


@router.put("/me/password")
async def update_current_user_password(
    password_update: schemas.UserUpdatePassword,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> dict[str, Any]:
    """Update current user password."""
    try:
        service.auth_service.update_password(db, current_user, password_update)
        return {"message": "Password updated successfully"}
    except IncorrectPasswordException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


# Health check endpoint for auth module
@router.get("/health")
async def auth_health_check() -> dict[str, str]:
    """Auth module health check."""
    return {"status": "healthy", "module": "auth"}
