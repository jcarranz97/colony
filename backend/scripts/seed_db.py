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
from app.cycles import schemas as cycle_schemas, service as cycle_service_module

# These imports ensure SQLAlchemy's mapper can resolve all relationships
# before any query runs, and that create_all creates every table.
from app.cycles.models import Cycle, CycleExpense, ExchangeRate  # noqa: F401
from app.database import Base, SessionLocal, engine
from app.households.models import Household, UserHouseholdMembership
from app.payment_methods.models import PaymentMethod
from app.recurrent_expenses.models import RecurrentExpense
from app.recurrent_incomes.models import RecurrentIncome


def create_tables() -> None:
    """Create all database tables if they do not already exist."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


def seed_household(db: Session, name: str) -> Household:
    """Return an existing household or create a new one.

    Args:
        db: Active SQLAlchemy session.
        name: The household name.

    Returns:
        The existing or newly created Household instance.
    """
    existing = db.query(Household).filter(Household.name == name).first()
    if existing:
        print(f"  ⏭️  Household '{name}' already exists, skipping.")
        return existing

    household = Household(name=name)
    db.add(household)
    db.flush()
    print(f"  ✅ Created household '{name}'.")
    return household


def seed_membership(
    db: Session, user: User, household: Household
) -> UserHouseholdMembership:
    """Link a user to a household if not already a member.

    Args:
        db: Active SQLAlchemy session.
        user: The User instance.
        household: The Household instance.

    Returns:
        The existing or newly created UserHouseholdMembership instance.
    """
    existing = (
        db.query(UserHouseholdMembership)
        .filter(
            UserHouseholdMembership.user_id == user.id,
            UserHouseholdMembership.household_id == household.id,
        )
        .first()
    )
    if existing:
        return existing

    membership = UserHouseholdMembership(user_id=user.id, household_id=household.id)
    db.add(membership)
    db.flush()
    print(f"    ✅ Added '{user.username}' to household '{household.name}'.")
    return membership


def ensure_default_admin(db: Session, household: Household) -> User:
    """Create the default admin user if it does not already exist.

    The admin is assigned to the given household and has their active
    household set to it.

    Credentials are read from env vars DEFAULT_ADMIN_USERNAME and
    DEFAULT_ADMIN_PASSWORD. This function is always called on startup
    regardless of SEED_MODE.

    Args:
        db: Active SQLAlchemy session.
        household: The Household to assign the admin to.

    Returns:
        The admin User instance.
    """
    username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "colony-admin")

    admin = db.query(User).filter(User.username == username).first()
    if admin:
        if admin.role != "admin":
            admin.role = "admin"
            db.commit()
            print(f"  ✅ Updated admin user '{username}' role to 'admin'.")
        else:
            print(f"  ⏭️  Admin user '{username}' already exists, skipping.")
    else:
        admin = User(
            username=username,
            password_hash=get_password_hash(password),
            preferred_currency="USD",
            locale="en-US",
            role="admin",
        )
        db.add(admin)
        db.flush()
        print(f"  ✅ Created admin user '{username}'.")

    seed_membership(db, admin, household)
    if admin.active_household_id is None:
        admin.active_household_id = household.id
        db.flush()

    return admin


def seed_user(db: Session, user_data: dict[str, Any], household: Household) -> User:
    """Return the existing user or create a new one from seed data.

    The user is assigned to the given household and has their active
    household set to it.

    Args:
        db: Active SQLAlchemy session.
        user_data: Dictionary of user fields from the seed YAML.
        household: The Household to assign the user to.

    Returns:
        The existing or newly created User instance.
    """
    username = user_data["username"]
    user = db.query(User).filter(User.username == username).first()

    if user:
        print(f"  ⏭️  User '{username}' already exists, skipping.")
    else:
        user = User(
            username=username,
            password_hash=get_password_hash(user_data["password"]),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            preferred_currency=user_data.get("preferred_currency", "USD"),
            locale=user_data.get("locale", "en-US"),
            role=user_data.get("role", "user"),
        )
        db.add(user)
        db.flush()
        print(f"  ✅ Created user '{username}'.")

    seed_membership(db, user, household)
    if user.active_household_id is None:
        user.active_household_id = household.id
        db.flush()

    return user


def seed_payment_method(
    db: Session, household: Household, pm_data: dict[str, Any]
) -> PaymentMethod:
    """Create a payment method for the household if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        household: The Household instance to associate the payment method with.
        pm_data: Dictionary of payment method fields from the seed YAML.

    Returns:
        The existing or newly created PaymentMethod instance.
    """
    name = pm_data["name"]
    existing = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.household_id == household.id,
            PaymentMethod.name == name,
            PaymentMethod.active,
        )
        .first()
    )

    if existing:
        print(f"    ⏭️  Payment method '{name}' already exists, skipping.")
        return existing

    pm = PaymentMethod(
        household_id=household.id,
        name=name,
        method_type=pm_data["method_type"],
        default_currency=pm_data["default_currency"],
        description=pm_data.get("description"),
    )
    db.add(pm)
    db.flush()
    print(f"    ✅ Created payment method '{name}'.")
    return pm


def seed_recurrent_expense(
    db: Session,
    household: Household,
    payment_method: PaymentMethod,
    tmpl_data: dict[str, Any],
) -> None:
    """Create a recurrent expense for the household if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        household: The Household instance to associate the recurrent expense with.
        payment_method: The PaymentMethod instance to use.
        tmpl_data: Dictionary of recurrent expense fields from the seed YAML.
    """
    description = tmpl_data["description"]
    existing = (
        db.query(RecurrentExpense)
        .filter(
            RecurrentExpense.household_id == household.id,
            RecurrentExpense.description == description,
            RecurrentExpense.active,
        )
        .first()
    )

    if existing:
        print(f"      ⏭️  Recurrent expense '{description}' already exists, skipping.")
        return

    db.add(
        RecurrentExpense(
            household_id=household.id,
            payment_method_id=payment_method.id,
            description=description,
            currency=tmpl_data["currency"],
            base_amount=Decimal(str(tmpl_data["base_amount"])),
            category=tmpl_data["category"],
            recurrence_type=tmpl_data["recurrence_type"],
            recurrence_config=tmpl_data.get("recurrence_config", {}),
            reference_date=date.fromisoformat(tmpl_data["reference_date"]),
            autopay=tmpl_data.get("autopay", False),
        )
    )
    print(f"      ✅ Created recurrent expense '{description}'.")


def seed_recurrent_income(
    db: Session,
    household: Household,
    payment_method: PaymentMethod,
    tmpl_data: dict[str, Any],
) -> None:
    """Create a recurrent income for the household if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
        household: The Household instance to associate the recurrent income with.
        payment_method: The PaymentMethod instance to use.
        tmpl_data: Dictionary of recurrent income fields from the seed YAML.
    """
    description = tmpl_data["description"]
    existing = (
        db.query(RecurrentIncome)
        .filter(
            RecurrentIncome.household_id == household.id,
            RecurrentIncome.description == description,
            RecurrentIncome.active,
        )
        .first()
    )

    if existing:
        print(f"      ⏭️  Recurrent income '{description}' already exists, skipping.")
        return

    db.add(
        RecurrentIncome(
            household_id=household.id,
            payment_method_id=payment_method.id,
            description=description,
            currency=tmpl_data["currency"],
            base_amount=Decimal(str(tmpl_data["base_amount"])),
            recurrence_type=tmpl_data["recurrence_type"],
            recurrence_config=tmpl_data.get("recurrence_config", {}),
            reference_date=date.fromisoformat(tmpl_data["reference_date"]),
        )
    )
    print(f"      ✅ Created recurrent income '{description}'.")


def seed_exchange_rate(db: Session, rate_data: dict[str, Any]) -> None:
    """Create an exchange rate record if one does not already exist for the date.

    Args:
        db: Active SQLAlchemy session.
        rate_data: Dict with keys ``from_currency``, ``to_currency``, ``rate``,
            and ``rate_date``.
    """
    from_c = rate_data["from_currency"]
    to_c = rate_data["to_currency"]
    rate_date = date.fromisoformat(rate_data["rate_date"])

    existing = (
        db.query(ExchangeRate)
        .filter(
            ExchangeRate.from_currency == from_c,
            ExchangeRate.to_currency == to_c,
            ExchangeRate.rate_date == rate_date,
        )
        .first()
    )

    if existing:
        print(
            f"  ⏭️  Exchange rate {from_c}→{to_c} on {rate_date} "
            "already exists, skipping."
        )
        return

    db.add(
        ExchangeRate(
            from_currency=from_c,
            to_currency=to_c,
            rate=Decimal(str(rate_data["rate"])),
            rate_date=rate_date,
        )
    )
    db.flush()
    print(
        f"  ✅ Created exchange rate {from_c}→{to_c} "
        f"= {rate_data['rate']} ({rate_date})."
    )


def seed_cycle(db: Session, household: Household, cycle_data: dict[str, Any]) -> None:
    """Create a cycle (with generated expenses) for the household if not existing.

    Uses the cycle service so that template generation, remaining balance
    calculation, and all business rules are applied consistently.

    Args:
        db: Active SQLAlchemy session.
        household: The Household instance to associate the cycle with.
        cycle_data: Dict of cycle fields from the seed YAML.
    """
    name = cycle_data["name"]
    existing = (
        db.query(Cycle)
        .filter(
            Cycle.household_id == household.id,
            Cycle.name == name,
            Cycle.active.is_(True),
        )
        .first()
    )

    if existing:
        print(f"    ⏭️  Cycle '{name}' already exists, skipping.")
        return

    create_schema = cycle_schemas.CycleCreate(
        name=name,
        start_date=date.fromisoformat(cycle_data["start_date"]),
        end_date=date.fromisoformat(cycle_data["end_date"]),
        generate_from_templates=cycle_data.get("generate_from_templates", False),
    )

    try:
        cycle = cycle_service_module.cycle_service.create_cycle(
            db, create_schema, str(household.id)
        )
    except Exception as exc:
        print(f"    ⚠️  Failed to create cycle '{name}': {exc}")
        db.rollback()
        return

    desired_status = cycle_data.get("status", "draft")
    if desired_status != "draft":
        cycle.status = desired_status
        db.commit()

    expense_count = sum(1 for e in cycle.expenses if e.active)
    print(
        f"    ✅ Created cycle '{name}' [{desired_status}] "
        f"with {expense_count} generated expense(s)."
    )


def _seed_household_full_data(
    db: Session, household: Household, user_data: dict[str, Any]
) -> None:
    """Seed payment methods, recurrent expenses, and cycles for a household."""
    payment_methods: dict[str, PaymentMethod] = {}
    for pm_data in user_data.get("payment_methods", []):
        pm = seed_payment_method(db, household, pm_data)
        payment_methods[pm.name] = pm

    for tmpl_data in user_data.get("recurrent_expenses", []):
        pm_name = tmpl_data.pop("payment_method_name")
        pm = payment_methods.get(pm_name)
        if pm is None:
            print(
                f"      ⚠️  Payment method '{pm_name}' not found for "
                f"recurrent expense '{tmpl_data.get('description')}', skipping."
            )
            continue
        seed_recurrent_expense(db, household, pm, tmpl_data)

    for tmpl_data in user_data.get("recurrent_incomes", []):
        pm_name = tmpl_data.pop("payment_method_name")
        pm = payment_methods.get(pm_name)
        if pm is None:
            print(
                f"      ⚠️  Payment method '{pm_name}' not found for "
                f"recurrent income '{tmpl_data.get('description')}', skipping."
            )
            continue
        seed_recurrent_income(db, household, pm, tmpl_data)

    db.commit()  # commit templates before generating cycle expenses

    for cycle_data in user_data.get("cycles", []):
        seed_cycle(db, household, cycle_data)


def seed_database(seed_file: Path, auth_only: bool = False) -> None:
    """Seed the database with initial development data from a YAML file.

    The operation is idempotent: records that already exist are skipped.

    Args:
        seed_file: Path to the YAML seed file.
        auth_only: When True, only user accounts are created — payment
            methods, recurrent expenses, cycles, and exchange rates are
            skipped.
    """
    create_tables()

    if auth_only:
        print("Seed mode: auth_only — only user credentials will be created.")
    else:
        print("Seed mode: full — all example data will be created.")

    print(f"Loading seed data from {seed_file}...")
    with seed_file.open() as f:
        data = yaml.safe_load(f)

    with SessionLocal() as db:
        # Seed households first so users and data can reference them
        households: dict[str, Household] = {}
        for hh_data in data.get("households", []):
            hh = seed_household(db, hh_data["name"])
            households[hh.name] = hh
        db.commit()

        # Ensure the default admin exists and is in the first/default household
        default_household_name = next(iter(households), None)
        default_household = (
            households[default_household_name]
            if default_household_name
            else seed_household(db, "Default Household")
        )
        print("Ensuring default admin user exists...")
        ensure_default_admin(db, default_household)
        db.commit()

        if not auth_only:
            rates_data = data.get("exchange_rates", [])
            if rates_data:
                print(f"Processing {len(rates_data)} exchange rate(s)...")
                for rate_data in rates_data:
                    seed_exchange_rate(db, rate_data)
                db.commit()

        users_data = data.get("users", [])
        print(f"Processing {len(users_data)} user(s)...")

        for user_data in users_data:
            household_name = user_data.get("household", default_household_name)
            household = households.get(household_name or "", default_household)
            seed_user(db, user_data, household)
            if auth_only:
                db.commit()
                continue
            _seed_household_full_data(db, household, user_data)

        db.commit()

    print("✅ Seed data loaded successfully!")


if __name__ == "__main__":
    seed_file_path = Path(os.getenv("SEED_FILE", "../seed_data.yaml"))
    seed_mode = os.getenv("SEED_MODE", "full").strip().lower()
    seed_database(seed_file_path, auth_only=(seed_mode == "auth_only"))
