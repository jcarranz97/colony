"""Database seed script for loading initial development data."""

import os
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.database import Base, SessionLocal, engine
from app.payment_methods.models import PaymentMethod


def create_tables() -> None:
    """Create all database tables if they do not already exist."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


def seed_user(db: Session, user_data: dict[str, Any]) -> User:
    """Return the existing user or create a new one from seed data.

    Args:
        db: Active SQLAlchemy session.
        user_data: Dictionary of user fields from the seed YAML.

    Returns:
        The existing or newly created User instance.
    """
    email = user_data["email"]
    user = db.query(User).filter(User.email == email).first()

    if user:
        print(f"  ⏭️  User '{email}' already exists, skipping.")
        return user

    user = User(
        email=email,
        password_hash=get_password_hash(user_data["password"]),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        preferred_currency=user_data.get("preferred_currency", "USD"),
        locale=user_data.get("locale", "en-US"),
    )
    db.add(user)
    db.flush()  # populate user.id before inserting payment methods
    print(f"  ✅ Created user '{email}'.")
    return user


def seed_payment_method(db: Session, user: User, pm_data: dict[str, Any]) -> None:
    """Create a payment method for the user if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        user: The User instance to associate the payment method with.
        pm_data: Dictionary of payment method fields from the seed YAML.
    """
    name = pm_data["name"]
    exists = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == user.id,
            PaymentMethod.name == name,
            PaymentMethod.active,
        )
        .first()
    )

    if exists:
        print(f"    ⏭️  Payment method '{name}' already exists, skipping.")
        return

    db.add(
        PaymentMethod(
            user_id=user.id,
            name=name,
            method_type=pm_data["method_type"],
            default_currency=pm_data["default_currency"],
            description=pm_data.get("description"),
        )
    )
    print(f"    ✅ Created payment method '{name}'.")


def seed_database(seed_file: Path) -> None:
    """Seed the database with initial development data from a YAML file.

    The operation is idempotent: records that already exist are skipped.

    Args:
        seed_file: Path to the YAML seed file.
    """
    create_tables()

    print(f"Loading seed data from {seed_file}...")
    with seed_file.open() as f:
        data = yaml.safe_load(f)

    with SessionLocal() as db:
        users_data = data.get("users", [])
        print(f"Processing {len(users_data)} user(s)...")

        for user_data in users_data:
            user = seed_user(db, user_data)
            for pm_data in user_data.get("payment_methods", []):
                seed_payment_method(db, user, pm_data)

        db.commit()

    print("✅ Seed data loaded successfully!")


if __name__ == "__main__":
    seed_file_path = Path(os.getenv("SEED_FILE", "../seed_data.yaml"))
    seed_database(seed_file_path)
