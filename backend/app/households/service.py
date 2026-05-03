import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User

from .exceptions import (
    HouseholdNameExistsExceptionError,
    HouseholdNotFoundExceptionError,
    UserAlreadyInHouseholdExceptionError,
    UserNotInHouseholdExceptionError,
)
from .models import Household, UserHouseholdMembership

logger = logging.getLogger(__name__)


class HouseholdService:
    """Business logic for household management."""

    @staticmethod
    def create_household(db: Session, name: str) -> Household:
        """Create a new household.

        Args:
            db: Active database session.
            name: The household name (must be unique among active households).

        Returns:
            Newly created Household instance.

        Raises:
            HouseholdNameExistsExceptionError: If the name is already taken.
        """
        existing = (
            db.query(Household)
            .filter(Household.name == name, Household.active.is_(True))
            .first()
        )
        if existing:
            raise HouseholdNameExistsExceptionError(name)

        household = Household(name=name)
        try:
            db.add(household)
            db.commit()
            db.refresh(household)
        except IntegrityError as exc:
            db.rollback()
            raise HouseholdNameExistsExceptionError(name) from exc

        logger.info("Household created", extra={"household_id": str(household.id)})
        return household

    @staticmethod
    def get_households(db: Session, active: bool | None = None) -> list[Household]:
        """Return all households with optional active filter.

        Args:
            db: Active database session.
            active: If provided, filter by active status.

        Returns:
            List of Household instances ordered by name.
        """
        query = db.query(Household)
        if active is not None:
            query = query.filter(Household.active == active)
        return query.order_by(Household.name).all()

    @staticmethod
    def get_household_by_id(db: Session, household_id: UUID) -> Household:
        """Return an active household by UUID.

        Args:
            db: Active database session.
            household_id: UUID of the household.

        Returns:
            The Household instance.

        Raises:
            HouseholdNotFoundExceptionError: If not found or inactive.
        """
        household = (
            db.query(Household)
            .filter(
                Household.id == household_id,
                Household.active.is_(True),
            )
            .first()
        )
        if not household:
            raise HouseholdNotFoundExceptionError(household_id)
        return household

    @staticmethod
    def update_household(db: Session, household_id: UUID, name: str) -> Household:
        """Update a household's name.

        Args:
            db: Active database session.
            household_id: UUID of the household to update.
            name: New name for the household.

        Returns:
            Updated Household instance.

        Raises:
            HouseholdNotFoundExceptionError: If household does not exist.
            HouseholdNameExistsExceptionError: If the new name is taken.
        """
        household = HouseholdService.get_household_by_id(db, household_id)

        conflicting = (
            db.query(Household)
            .filter(
                Household.name == name,
                Household.active.is_(True),
                Household.id != household_id,
            )
            .first()
        )
        if conflicting:
            raise HouseholdNameExistsExceptionError(name)

        household.name = name
        db.commit()
        db.refresh(household)
        logger.info("Household updated", extra={"household_id": str(household_id)})
        return household

    @staticmethod
    def delete_household(db: Session, household_id: UUID) -> None:
        """Soft-delete a household.

        Args:
            db: Active database session.
            household_id: UUID of the household to deactivate.

        Raises:
            HouseholdNotFoundExceptionError: If the household does not exist.
        """
        household = HouseholdService.get_household_by_id(db, household_id)
        household.active = False
        db.commit()
        logger.info("Household deactivated", extra={"household_id": str(household_id)})

    @staticmethod
    def get_household_members(db: Session, household_id: UUID) -> list[User]:
        """Return all users that are members of the household.

        Args:
            db: Active database session.
            household_id: UUID of the household.

        Returns:
            List of User instances.

        Raises:
            HouseholdNotFoundExceptionError: If the household does not exist.
        """
        HouseholdService.get_household_by_id(db, household_id)
        memberships = (
            db.query(UserHouseholdMembership)
            .filter(UserHouseholdMembership.household_id == household_id)
            .all()
        )
        user_ids = [m.user_id for m in memberships]
        if not user_ids:
            return []
        return (
            db.query(User).filter(User.id.in_(user_ids)).order_by(User.username).all()
        )

    @staticmethod
    def add_user_to_household(db: Session, household_id: UUID, user_id: UUID) -> None:
        """Add a user to a household.

        Args:
            db: Active database session.
            household_id: Target household UUID.
            user_id: User UUID to add.

        Raises:
            HouseholdNotFoundExceptionError: If the household does not exist.
            UserAlreadyInHouseholdExceptionError: If the user is already a member.
        """
        HouseholdService.get_household_by_id(db, household_id)

        existing = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == user_id,
                UserHouseholdMembership.household_id == household_id,
            )
            .first()
        )
        if existing:
            raise UserAlreadyInHouseholdExceptionError(user_id, household_id)

        membership = UserHouseholdMembership(user_id=user_id, household_id=household_id)
        try:
            db.add(membership)
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyInHouseholdExceptionError(user_id, household_id) from exc

        user = db.query(User).filter(User.id == user_id).first()
        if user and user.active_household_id is None:
            user.active_household_id = household_id

        db.commit()
        logger.info(
            "User added to household",
            extra={
                "user_id": str(user_id),
                "household_id": str(household_id),
            },
        )

    @staticmethod
    def remove_user_from_household(
        db: Session, household_id: UUID, user_id: UUID
    ) -> None:
        """Remove a user from a household.

        Clears active_household_id on the user if it pointed to this household.

        Args:
            db: Active database session.
            household_id: Target household UUID.
            user_id: User UUID to remove.

        Raises:
            HouseholdNotFoundExceptionError: If the household does not exist.
            UserNotInHouseholdExceptionError: If the user is not a member.
        """
        HouseholdService.get_household_by_id(db, household_id)

        membership = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == user_id,
                UserHouseholdMembership.household_id == household_id,
            )
            .first()
        )
        if not membership:
            raise UserNotInHouseholdExceptionError(user_id, household_id)

        db.delete(membership)

        user = db.query(User).filter(User.id == user_id).first()
        if user and user.active_household_id == household_id:
            user.active_household_id = None

        db.commit()
        logger.info(
            "User removed from household",
            extra={
                "user_id": str(user_id),
                "household_id": str(household_id),
            },
        )

    @staticmethod
    def get_user_households(db: Session, user_id: UUID) -> list[Household]:
        """Return all active households the user belongs to.

        Args:
            db: Active database session.
            user_id: UUID of the user.

        Returns:
            List of active Household instances.
        """
        memberships = (
            db.query(UserHouseholdMembership)
            .filter(UserHouseholdMembership.user_id == user_id)
            .all()
        )
        household_ids = [m.household_id for m in memberships]
        if not household_ids:
            return []
        return (
            db.query(Household)
            .filter(
                Household.id.in_(household_ids),
                Household.active.is_(True),
            )
            .order_by(Household.name)
            .all()
        )

    @staticmethod
    def set_active_household(db: Session, user: User, household_id: UUID) -> User:
        """Set the active household for a user.

        The user must already be a member of the household.

        Args:
            db: Active database session.
            user: The User ORM instance to update.
            household_id: UUID of the household to activate.

        Returns:
            Updated User instance.

        Raises:
            HouseholdNotFoundExceptionError: If the household does not exist.
            UserNotInHouseholdExceptionError: If the user is not a member.
        """
        HouseholdService.get_household_by_id(db, household_id)

        membership = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == user.id,
                UserHouseholdMembership.household_id == household_id,
            )
            .first()
        )
        if not membership:
            raise UserNotInHouseholdExceptionError(user.id, household_id)

        user.active_household_id = household_id
        db.commit()
        db.refresh(user)
        logger.info(
            "Active household updated",
            extra={
                "user_id": str(user.id),
                "household_id": str(household_id),
            },
        )
        return user


household_service = HouseholdService()
