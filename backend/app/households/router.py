from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser, CurrentAdminUser
from app.dependencies import get_db

from . import schemas
from .exceptions import (
    HouseholdNameExistsExceptionError,
    HouseholdNotFoundExceptionError,
    UserAlreadyInHouseholdExceptionError,
    UserNotInHouseholdExceptionError,
)
from .service import household_service

router = APIRouter(prefix="/households", tags=["households"])

DatabaseDep = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Admin endpoints — household CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=schemas.HouseholdResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a household",
    description="Create a new household. Requires admin role.",
)
async def create_household(
    payload: schemas.HouseholdCreate,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> schemas.HouseholdResponse:
    """Create a new household. Admin only."""
    try:
        household = household_service.create_household(db, payload.name)
        return schemas.HouseholdResponse.model_validate(household)
    except HouseholdNameExistsExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/",
    response_model=list[schemas.HouseholdResponse],
    summary="List households",
    description="List all households. Requires admin role.",
)
async def list_households(
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> list[schemas.HouseholdResponse]:
    """List all households. Admin only."""
    households = household_service.get_households(db, active=True)
    return [schemas.HouseholdResponse.model_validate(h) for h in households]


@router.get(
    "/me",
    response_model=list[schemas.HouseholdResponse],
    summary="My households",
    description="Return all households the authenticated user belongs to.",
)
async def get_my_households(
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> list[schemas.HouseholdResponse]:
    """Return the caller's household memberships."""
    households = household_service.get_user_households(db, current_user.id)
    return [schemas.HouseholdResponse.model_validate(h) for h in households]


@router.put(
    "/me/active",
    response_model=schemas.HouseholdResponse,
    summary="Set active household",
    description=(
        "Switch the authenticated user's active household. "
        "The user must already be a member."
    ),
)
async def set_active_household(
    payload: schemas.SetActiveHouseholdRequest,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.HouseholdResponse:
    """Switch the caller's active household."""
    try:
        user = household_service.set_active_household(
            db, current_user, payload.household_id
        )
        household = household_service.get_household_by_id(
            db,
            user.active_household_id,  # type: ignore[arg-type]
        )
        return schemas.HouseholdResponse.model_validate(household)
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except UserNotInHouseholdExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{household_id}",
    response_model=schemas.HouseholdResponse,
    summary="Get household",
    description="Get a household by ID. Requires admin role.",
)
async def get_household(
    household_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> schemas.HouseholdResponse:
    """Retrieve a single household by ID. Admin only."""
    try:
        household = household_service.get_household_by_id(db, household_id)
        return schemas.HouseholdResponse.model_validate(household)
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put(
    "/{household_id}",
    response_model=schemas.HouseholdResponse,
    summary="Update household",
    description="Update a household's name. Requires admin role.",
)
async def update_household(
    household_id: UUID,
    payload: schemas.HouseholdUpdate,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> schemas.HouseholdResponse:
    """Update a household. Admin only."""
    if payload.name is None:
        household = household_service.get_household_by_id(db, household_id)
        return schemas.HouseholdResponse.model_validate(household)
    try:
        household = household_service.update_household(db, household_id, payload.name)
        return schemas.HouseholdResponse.model_validate(household)
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HouseholdNameExistsExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{household_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete household",
    description="Soft-delete a household. Requires admin role.",
)
async def delete_household(
    household_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> None:
    """Soft-delete a household. Admin only."""
    try:
        household_service.delete_household(db, household_id)
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin endpoints — member management
# ---------------------------------------------------------------------------


@router.get(
    "/{household_id}/members",
    response_model=list[schemas.HouseholdMemberResponse],
    summary="List household members",
    description="List all users in a household. Requires admin role.",
)
async def list_household_members(
    household_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> list[schemas.HouseholdMemberResponse]:
    """List members of a household. Admin only."""
    try:
        members = household_service.get_household_members(db, household_id)
        return [schemas.HouseholdMemberResponse.model_validate(u) for u in members]
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/{household_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=list[schemas.HouseholdMemberResponse],
    summary="Add member",
    description="Add a user to a household. Requires admin role.",
)
async def add_household_member(
    household_id: UUID,
    payload: schemas.AddMemberRequest,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> list[schemas.HouseholdMemberResponse]:
    """Add a user to a household. Admin only."""
    try:
        household_service.add_user_to_household(db, household_id, payload.user_id)
        members = household_service.get_household_members(db, household_id)
        return [schemas.HouseholdMemberResponse.model_validate(u) for u in members]
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except UserAlreadyInHouseholdExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{household_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="Remove a user from a household. Requires admin role.",
)
async def remove_household_member(
    household_id: UUID,
    user_id: UUID,
    _admin: CurrentAdminUser,
    db: DatabaseDep,
) -> None:
    """Remove a user from a household. Admin only."""
    try:
        household_service.remove_user_from_household(db, household_id, user_id)
    except HouseholdNotFoundExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except UserNotInHouseholdExceptionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
