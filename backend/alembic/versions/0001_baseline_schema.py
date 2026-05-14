"""baseline schema (pre-Alembic state).

Captures the schema produced by ``Base.metadata.create_all()`` as of the
adoption of Alembic. Fresh environments run this migration to create the
schema. Deployed environments (where the schema already exists) should
``alembic stamp 0001_baseline`` once instead — see
``docs/development/migrations.md``.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the original Colony schema from scratch."""
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "from_currency",
            postgresql.ENUM("USD", "MXN", name="currency_code"),
            nullable=False,
        ),
        sa.Column(
            "to_currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("rate", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rate > 0", name="check_exchange_rate_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_currency", "to_currency", "rate_date", name="unique_currency_date"
        ),
    )
    op.create_table(
        "households",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cycles",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "remaining_balance", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "ACTIVE", "COMPLETED", name="cycle_status"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("end_date > start_date", name="valid_cycle_dates"),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "name", name="unique_household_cycle_name"),
    )
    op.create_table(
        "payment_methods",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "method_type",
            postgresql.ENUM(
                "DEBIT", "CREDIT", "CASH", "TRANSFER", name="paymentmethodtype"
            ),
            nullable=False,
        ),
        sa.Column(
            "default_currency",
            postgresql.ENUM("USD", "MXN", name="currencycode"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("last_4_digits", sa.String(length=4), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column(
            "preferred_currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("admin", "user", name="user_role"),
            nullable=False,
        ),
        sa.Column("active_household_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["active_household_id"], ["households.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "recurrent_expenses",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("payment_method_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column(
            "currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("base_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM("FIXED", "VARIABLE", "EXTRA", name="expense_category"),
            nullable=False,
        ),
        sa.Column(
            "recurrence_type",
            postgresql.ENUM(
                "WEEKLY",
                "BI_WEEKLY",
                "MONTHLY",
                "CUSTOM",
                name="recurrence_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "recurrence_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("autopay", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("base_amount > 0", name="check_base_amount_positive"),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recurrent_incomes",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("payment_method_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column(
            "currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("base_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "recurrence_type",
            postgresql.ENUM(
                "WEEKLY",
                "BI_WEEKLY",
                "MONTHLY",
                "CUSTOM",
                name="recurrence_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "recurrence_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("base_amount > 0", name="check_income_base_amount_positive"),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_household_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "household_id", name="unique_user_household"),
    )
    op.create_table(
        "cycle_expenses",
        sa.Column("cycle_id", sa.UUID(), nullable=False),
        sa.Column("template_id", sa.UUID(), nullable=True),
        sa.Column("payment_method_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column(
            "currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("amount_usd", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                "FIXED",
                "VARIABLE",
                "EXTRA",
                name="expense_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("autopay", sa.Boolean(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "PAID",
                "CANCELLED",
                "OVERDUE",
                "PAID_OTHER",
                "SKIPPED",
                name="expense_status",
            ),
            nullable=False,
        ),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("paid", sa.Boolean(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("amount > 0", name="check_expense_amount_positive"),
        sa.CheckConstraint("amount_usd > 0", name="check_expense_amount_usd_positive"),
        sa.ForeignKeyConstraint(["cycle_id"], ["cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["recurrent_expenses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cycle_incomes",
        sa.Column("cycle_id", sa.UUID(), nullable=False),
        sa.Column("template_id", sa.UUID(), nullable=True),
        sa.Column("payment_method_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column(
            "currency",
            postgresql.ENUM("USD", "MXN", name="currency_code", create_type=False),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("amount_usd", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("income_date", sa.Date(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("amount > 0", name="check_income_amount_positive"),
        sa.CheckConstraint("amount_usd > 0", name="check_income_amount_usd_positive"),
        sa.ForeignKeyConstraint(["cycle_id"], ["cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"]),
        sa.ForeignKeyConstraint(
            ["template_id"], ["recurrent_incomes.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the entire schema."""
    op.drop_table("cycle_incomes")
    op.drop_table("cycle_expenses")
    op.drop_table("user_household_memberships")
    op.drop_table("recurrent_incomes")
    op.drop_table("recurrent_expenses")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_table("payment_methods")
    op.drop_table("cycles")
    op.drop_table("households")
    op.drop_table("exchange_rates")
    for enum_name in (
        "expense_status",
        "expense_category",
        "recurrence_type",
        "cycle_status",
        "currencycode",
        "paymentmethodtype",
        "user_role",
        "currency_code",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
