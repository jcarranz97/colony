from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models, schemas, utils
from .config import auth_settings
from .exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    InactiveUserException,
    IncorrectPasswordException
)

class AuthService:

    @staticmethod
    def create_user(db: Session, user_create: schemas.UserCreate) -> models.User:
        """Create a new user."""
        # Check if user already exists
        existing_user = db.query(models.User).filter(
            models.User.email == user_create.email
        ).first()

        if existing_user:
            raise UserAlreadyExistsException(user_create.email)

        # Hash password
        hashed_password = utils.get_password_hash(user_create.password)

        # Create user
        db_user = models.User(
            email=user_create.email,
            password_hash=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            preferred_currency=user_create.preferred_currency,
            locale=user_create.locale
        )

        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise UserAlreadyExistsException(user_create.email)

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> models.User:
        """Authenticate user with email and password."""
        print("Authenticating user:", email)
        user = db.query(models.User).filter(
            models.User.email == email,
            models.User.active == True
        ).first()

        if not user:
            raise InvalidCredentialsException()

        if not utils.verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email."""
        return db.query(models.User).filter(
            models.User.email == email,
            models.User.active == True
        ).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[models.User]:
        """Get user by ID."""
        return db.query(models.User).filter(
            models.User.id == user_id,
            models.User.active == True
        ).first()

    @staticmethod
    def update_user(db: Session, user: models.User, user_update: schemas.UserUpdate) -> models.User:
        """Update user information."""
        update_data = user_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(
        db: Session,
        user: models.User,
        password_update: schemas.UserUpdatePassword
    ) -> models.User:
        """Update user password."""
        # Verify current password
        if not utils.verify_password(password_update.current_password, user.password_hash):
            raise IncorrectPasswordException()

        # Hash new password
        new_password_hash = utils.get_password_hash(password_update.new_password)
        user.password_hash = new_password_hash

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_access_token(user: models.User) -> schemas.Token:
        """Create access token for user."""
        access_token_expires = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = utils.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )

        return schemas.Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )

# Create service instance
auth_service = AuthService()
