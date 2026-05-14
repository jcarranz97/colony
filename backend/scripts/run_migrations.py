"""Apply pending Alembic migrations to the configured database.

Auto-stamps the baseline revision if it detects a pre-Alembic schema —
tables already created via the legacy ``Base.metadata.create_all()``
path but no ``alembic_version`` table yet. This lets the existing
deployments adopt Alembic without a manual one-time stamp step.

Invoked from the Helm chart's ``run-migrations`` init container.
"""

from __future__ import annotations

import sys

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.database import engine

BASELINE_REVISION = "0001_baseline"


def main() -> int:
    """Stamp baseline if needed, then upgrade to head."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    alembic_cfg = Config("alembic.ini")

    has_alembic_state = "alembic_version" in table_names
    has_pre_alembic_data = "households" in table_names

    if not has_alembic_state and has_pre_alembic_data:
        print(
            f"Detected pre-Alembic schema; stamping {BASELINE_REVISION} so "
            "the activity-log migration applies on top of the existing tables."
        )
        command.stamp(alembic_cfg, BASELINE_REVISION)
    elif not has_alembic_state:
        print("Fresh database — running every migration from zero.")
    else:
        print("Alembic state present — applying any pending migrations.")

    command.upgrade(alembic_cfg, "head")
    print("Migrations complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
