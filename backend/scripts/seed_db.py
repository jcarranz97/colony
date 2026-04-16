"""Database seed script for loading initial development data."""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.database import Base, SessionLocal, engine

# ExpenseTemplate must be imported so SQLAlchemy's mapper can resolve the
# relationship declared on User and PaymentMethod before any query runs.
from app.expense_templates.models import ExpenseTemplate
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


def seed_payment_method(
    db: Session, user: User, pm_data: dict[str, Any]
) -> PaymentMethod:
    """Create a payment method for the user if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        user: The User instance to associate the payment method with.
        pm_data: Dictionary of payment method fields from the seed YAML.

    Returns:
        The existing or newly created PaymentMethod instance.
    """
    name = pm_data["name"]
    existing = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == user.id,
            PaymentMethod.name == name,
            PaymentMethod.active,
        )
        .first()
    )

    if existing:
        print(f"    ⏭️  Payment method '{name}' already exists, skipping.")
        return existing

    pm = PaymentMethod(
        user_id=user.id,
        name=name,
        method_type=pm_data["method_type"],
        default_currency=pm_data["default_currency"],
        description=pm_data.get("description"),
    )
    db.add(pm)
    db.flush()
    print(f"    ✅ Created payment method '{name}'.")
    return pm


def seed_expense_template(
    db: Session,
    user: User,
    payment_method: PaymentMethod,
    tmpl_data: dict[str, Any],
) -> None:
    """Create an expense template for the user if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        user: The User instance to associate the template with.
        payment_method: The PaymentMethod instance to use.
        tmpl_data: Dictionary of template fields from the seed YAML.
    """
    description = tmpl_data["description"]
    existing = (
        db.query(ExpenseTemplate)
        .filter(
            ExpenseTemplate.user_id == user.id,
            ExpenseTemplate.description == description,
            ExpenseTemplate.active,
        )
        .first()
    )

    if existing:
        print(f"      ⏭️  Expense template '{description}' already exists, skipping.")
        return

    db.add(
        ExpenseTemplate(
            user_id=user.id,
            payment_method_id=payment_method.id,
            description=description,
            currency=tmpl_data["currency"],
            base_amount=Decimal(str(tmpl_data["base_amount"])),
            category=tmpl_data["category"],
            recurrence_type=tmpl_data["recurrence_type"],
            recurrence_config=tmpl_data.get("recurrence_config", {}),
            reference_date=date.fromisoformat(tmpl_data["reference_date"]),
            autopay_info=tmpl_data.get("autopay_info"),
        )
    )
    print(f"      ✅ Created expense template '{description}'.")


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

            # Build a name→PaymentMethod lookup for template cross-referencing
            payment_methods: dict[str, PaymentMethod] = {}
            for pm_data in user_data.get("payment_methods", []):
                pm = seed_payment_method(db, user, pm_data)
                payment_methods[pm.name] = pm

            for tmpl_data in user_data.get("expense_templates", []):
                pm_name = tmpl_data.pop("payment_method_name")
                pm = payment_methods.get(pm_name)
                if pm is None:
                    print(
                        f"      ⚠️  Payment method '{pm_name}' not found for "
                        f"template '{tmpl_data.get('description')}', skipping."
                    )
                    continue
                seed_expense_template(db, user, pm, tmpl_data)

        db.commit()

    print("✅ Seed data loaded successfully!")


if __name__ == "__main__":
    seed_file_path = Path(os.getenv("SEED_FILE", "../seed_data.yaml"))
    seed_database(seed_file_path)
