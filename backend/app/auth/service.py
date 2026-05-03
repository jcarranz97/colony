from datetime import timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas, utils
from .config import auth_settings
from .constants import JWT_TOKEN_PREFIX
from .exceptions import (
    IncorrectPasswordExceptionError,
    InvalidCredentialsExceptionError,
    UserAlreadyExistsExceptionError,
    UserNotFoundExceptionError,
)


class AuthService:
    """Authentication service for user management and token handling."""

    @staticmethod
    def create_user(db: Session, user_create: schemas.UserCreate) -> models.User:
        """Create a new user."""
        existing_user = (
            db.query(models.User)
            .filter(models.User.username == user_create.username)
            .first()
        )

        if existing_user:
            raise UserAlreadyExistsExceptionError(user_create.username)

        hashed_password = utils.get_password_hash(user_create.password)

        db_user = models.User(
            username=user_create.username,
            password_hash=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            preferred_currency=user_create.preferred_currency,
            locale=user_create.locale,
            role=user_create.role,
        )

        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            db.rollback()
            raise UserAlreadyExistsExceptionError(user_create.username) from e

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> models.User:
        """Authenticate user with username and password."""
        user = (
            db.query(models.User)
            .filter(models.User.username == username, models.User.active)
            .first()
        )

        if not user:
            raise InvalidCredentialsExceptionError

        if not utils.verify_password(password, user.password_hash):
            raise InvalidCredentialsExceptionError

        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> models.User | None:
        """Get user by username."""
        return (
            db.query(models.User)
            .filter(models.User.username == username, models.User.active)
            .first()
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> models.User | None:
        """Get user by ID."""
        return (
            db.query(models.User)
            .filter(models.User.id == user_id, models.User.active)
            .first()
        )

    @staticmethod
    def update_user(
        db: Session, user: models.User, user_update: schemas.UserUpdate
    ) -> models.User:
        """Update user information."""
        update_data = user_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(
        db: Session, user: models.User, password_update: schemas.UserUpdatePassword
    ) -> models.User:
        """Update user password."""
        if not utils.verify_password(
            password_update.current_password, user.password_hash
        ):
            raise IncorrectPasswordExceptionError

        new_password_hash = utils.get_password_hash(password_update.new_password)
        user.password_hash = new_password_hash

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_all_users(db: Session) -> list[models.User]:
        """Return all users (including inactive) ordered by creation date."""
        return db.query(models.User).order_by(models.User.created_at).all()

    @staticmethod
    def get_user_by_id_admin(db: Session, user_id: UUID) -> models.User:
        """Get any user by ID (admin view — includes inactive users)."""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise UserNotFoundExceptionError
        return user

    @staticmethod
    def update_user_admin(
        db: Session,
        user: models.User,
        update: schemas.UserAdminUpdate,
    ) -> models.User:
        """Apply admin update (can change role and active status)."""
        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_access_token(user: models.User) -> schemas.Token:
        """Create access token for user."""
        access_token_expires = timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = utils.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return schemas.Token(
            access_token=access_token,
            token_type=JWT_TOKEN_PREFIX,
            expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            * 60,  # Convert to seconds
        )


# Create service instance
auth_service = AuthService()
