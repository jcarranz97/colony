"""Helpers for computing diffs between SQLAlchemy model field states.

The diff format ``{field: {"from": old, "to": new}}`` is what's stored on
``ActivityLog.changes``. Values are JSON-serialized using a permissive
encoder that handles UUIDs, datetimes, dates, decimals, and enums.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def _serialize(value: Any) -> Any:  # noqa: ANN401, PLR0911 - intentional Any; many returns are clearer than dispatch dict
    """Convert a value to a JSON-safe form for the changes JSONB column."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list | tuple):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    return str(value)


def compute_diff(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compute a ``{field: {"from", "to"}}`` diff between two field-state dicts.

    Only fields present in *both* dicts are compared. Use the intersection of
    keys if you want to track only a subset of fields (e.g. the keys of the
    Pydantic ``model_dump(exclude_unset=True)`` output).
    """
    diff: dict[str, dict[str, Any]] = {}
    for key in before.keys() & after.keys():
        if before[key] != after[key]:
            diff[key] = {
                "from": _serialize(before[key]),
                "to": _serialize(after[key]),
            }
    return diff
