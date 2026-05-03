from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db

from . import schemas, service
from .dependencies import CurrentActiveUser, CurrentAdminUser
from .exceptions import (
    IncorrectPasswordExceptionError,
    InvalidCredentialsExceptionError,
    UserAlreadyExistsExceptionError,
    UserNotFoundExceptionError,
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
    user_data: schemas.UserCreate,
    db: DatabaseDep,
    _admin: CurrentAdminUser,
) -> schemas.UserResponse:
    """Create a new user. Requires admin role."""
    try:
        user = service.auth_service.create_user(db, user_data)
        return schemas.UserResponse.from_orm(user)
    except UserAlreadyExistsExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DatabaseDep,
) -> schemas.Token:
    """Login user and return access token."""
    try:
        user = service.auth_service.authenticate_user(
            db,
            username=form_data.username,
            password=form_data.password,
        )

        return service.auth_service.create_access_token(user)

    except InvalidCredentialsExceptionError as e:
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
    except IncorrectPasswordExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


# Admin user management endpoints
@router.get("/users", response_model=list[schemas.UserResponse])
async def list_users(
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> list[schemas.UserResponse]:
    """List all users. Requires admin role."""
    return service.auth_service.list_all_users(db)  # type: ignore[return-value]


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> schemas.UserResponse:
    """Get a user by ID. Requires admin role."""
    try:
        return service.auth_service.get_user_by_id_admin(db, user_id)  # type: ignore[return-value]
    except UserNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: UUID,
    user_update: schemas.UserAdminUpdate,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> schemas.UserResponse:
    """Update a user. Requires admin role."""
    try:
        user = service.auth_service.get_user_by_id_admin(db, user_id)
        return service.auth_service.update_user_admin(db, user, user_update)  # type: ignore[return-value]
    except UserNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> None:
    """Deactivate a user (soft delete). Requires admin role."""
    try:
        user = service.auth_service.get_user_by_id_admin(db, user_id)
        user.active = False
        db.commit()
    except UserNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


# Health check endpoint for auth module
@router.get("/health")
async def auth_health_check() -> dict[str, str]:
    """Auth module health check."""
    return {"status": "healthy", "module": "auth"}
