"""Alembic environment configuration.

Wires Alembic to the application's SQLAlchemy metadata and DB URL so
migrations work with `uv run alembic upgrade head` in any environment
that sets DATABASE_URL.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import all model modules so Base.metadata is fully populated before
# autogenerate runs. The order doesn't matter — only that every model
# class has been imported.
from app.activity import models as _activity_models  # noqa: F401
from app.auth import models as _auth_models  # noqa: F401
from app.config import settings
from app.cycles import models as _cycles_models  # noqa: F401
from app.database import Base
from app.households import models as _households_models  # noqa: F401
from app.payment_methods import models as _payment_methods_models  # noqa: F401
from app.recurrent_expenses import models as _recurrent_expenses_models  # noqa: F401
from app.recurrent_incomes import models as _recurrent_incomes_models  # noqa: F401

config = context.config

# Override sqlalchemy.url from app settings so deployments don't need
# to maintain a duplicate DB URL in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emits SQL without a DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the configured DB."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
