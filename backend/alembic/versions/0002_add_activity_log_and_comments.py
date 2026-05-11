"""add activity log and comments.

Adds two new tables that support JIRA-style history feeds and per-entity
comments. Both reference entities polymorphically via
``(entity_type, entity_id)``; no DB-level FK is enforced for the entity
target because it can be any of payment_method, recurrent_expense,
recurrent_income, cycle, cycle_expense, or cycle_income.

Revision ID: 0002_activity_and_comments
Revises: 0001_baseline
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_activity_and_comments"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create activity_log and comments tables with their indexes."""
    op.create_table(
        "activity_log",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("cycle_id", sa.UUID(), nullable=True),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column(
            "changes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cycle_id"], ["cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_activity_log_actor_created",
        "activity_log",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_log_cycle_created",
        "activity_log",
        ["cycle_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_log_entity_created",
        "activity_log",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_log_household_created",
        "activity_log",
        ["household_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "comments",
        sa.Column("household_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("cycle_id", sa.UUID(), nullable=True),
        sa.Column("author_user_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cycle_id"], ["cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["household_id"], ["households.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comments_cycle_created",
        "comments",
        ["cycle_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_comments_entity_created",
        "comments",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_comments_household_created",
        "comments",
        ["household_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop activity_log and comments tables and their indexes."""
    op.drop_index("ix_comments_household_created", table_name="comments")
    op.drop_index("ix_comments_entity_created", table_name="comments")
    op.drop_index("ix_comments_cycle_created", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_activity_log_household_created", table_name="activity_log")
    op.drop_index("ix_activity_log_entity_created", table_name="activity_log")
    op.drop_index("ix_activity_log_cycle_created", table_name="activity_log")
    op.drop_index("ix_activity_log_actor_created", table_name="activity_log")
    op.drop_table("activity_log")
