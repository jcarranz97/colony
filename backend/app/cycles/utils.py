"""Recurrence calculation utilities for expense templates.

Calculates due-date occurrences for each recurrence type without requiring
any external date library — only the standard-library ``datetime`` and
``calendar`` modules are used.
"""

import calendar
from datetime import date, timedelta
from typing import Any


def _add_months(dt: date, months: int) -> date:
    """Return a new date shifted by *months* calendar months.

    If the resulting month has fewer days than ``dt.day``, the last valid day
    of that month is used (e.g. 31 Jan + 1 month → 28/29 Feb).

    Args:
        dt: Starting date.
        months: Number of months to add (may be negative).

    Returns:
        New date shifted by the given number of months.
    """
    month_total = dt.month - 1 + months
    year = dt.year + month_total // 12
    month = month_total % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _add_years(dt: date, years: int) -> date:
    """Return a new date shifted by *years* years.

    Handles Feb-29 → Feb-28 when the target year is not a leap year.

    Args:
        dt: Starting date.
        years: Number of years to add.

    Returns:
        New date shifted by the given number of years.
    """
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        # Feb 29 in a non-leap target year → use Feb 28
        return dt.replace(year=dt.year + years, day=28)


def calculate_weekly_occurrences(
    config: dict[str, Any],
    cycle_start: date,
    cycle_end: date,
) -> list[date]:
    """Calculate weekly expense occurrence dates within a cycle period.

    Finds the first occurrence of ``day_of_week`` on or after *cycle_start*,
    then generates subsequent weekly dates until *cycle_end* (inclusive).

    Args:
        config: Recurrence config with ``day_of_week`` key (0=Sun … 6=Sat).
        cycle_start: First day of the cycle period.
        cycle_end: Last day of the cycle period (inclusive).

    Returns:
        Sorted list of occurrence dates within [cycle_start, cycle_end].
    """
    day_of_week: int = config["day_of_week"]
    occurrences: list[date] = []

    # Align day_of_week to Python's isoweekday convention: Mon=0 … Sun=6
    # The config uses Sun=0 … Sat=6; isoweekday uses Mon=1 … Sun=7.
    # Convert config dow → Python weekday: (day_of_week + 6) % 7
    python_weekday = (day_of_week + 6) % 7
    days_ahead = (python_weekday - cycle_start.weekday()) % 7
    current = cycle_start + timedelta(days=days_ahead)

    while current <= cycle_end:
        occurrences.append(current)
        current += timedelta(days=7)

    return occurrences


def calculate_bi_weekly_occurrences(
    config: dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date,
) -> list[date]:
    """Calculate bi-weekly (fixed-interval) occurrence dates within a cycle.

    Anchors to *reference_date* and steps backward until before *cycle_start*,
    then collects all dates within [cycle_start, cycle_end].

    Args:
        config: Recurrence config with ``interval_days`` key (positive int).
        reference_date: A known past occurrence used as the interval anchor.
        cycle_start: First day of the cycle period.
        cycle_end: Last day of the cycle period (inclusive).

    Returns:
        Sorted list of occurrence dates within [cycle_start, cycle_end].
    """
    interval: int = config["interval_days"]
    occurrences: list[date] = []

    current = reference_date
    # Walk backward to a date before or at cycle_start
    while current > cycle_start:
        current -= timedelta(days=interval)

    # Walk forward and collect dates inside the cycle window
    while current <= cycle_end:
        if current >= cycle_start:
            occurrences.append(current)
        current += timedelta(days=interval)

    return occurrences


def calculate_monthly_occurrences(
    config: dict[str, Any],
    cycle_start: date,
    cycle_end: date,
) -> list[date]:
    """Calculate monthly occurrence dates within a cycle period.

    Iterates over every calendar month that overlaps [cycle_start, cycle_end]
    and computes the occurrence date from ``day_of_month``.

    Args:
        config: Recurrence config with ``day_of_month`` (int 1-31) and
            optional ``handle_month_end`` (bool, default False).
        cycle_start: First day of the cycle period.
        cycle_end: Last day of the cycle period (inclusive).

    Returns:
        Sorted list of occurrence dates within [cycle_start, cycle_end].
    """
    day_of_month: int = config["day_of_month"]
    handle_month_end: bool = config.get("handle_month_end", False)
    occurrences: list[date] = []

    current_month = cycle_start.replace(day=1)

    while current_month <= cycle_end:
        max_day = calendar.monthrange(current_month.year, current_month.month)[1]
        if day_of_month > max_day:
            if handle_month_end:
                occurrence = current_month.replace(day=max_day)
            else:
                current_month = _add_months(current_month, 1)
                continue
        else:
            occurrence = current_month.replace(day=day_of_month)

        if cycle_start <= occurrence <= cycle_end:
            occurrences.append(occurrence)

        current_month = _add_months(current_month, 1)

    return occurrences


def calculate_custom_occurrences(
    config: dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date,
) -> list[date]:
    """Calculate custom-interval occurrence dates within a cycle period.

    Anchors to *reference_date* and steps by ``interval`` ``unit``s in both
    directions to find all occurrences within [cycle_start, cycle_end].

    Args:
        config: Recurrence config with ``interval`` (positive int) and
            ``unit`` (one of ``"days"``, ``"weeks"``, ``"months"``,
            ``"years"``).  For month/year units an optional ``day_of_month``
            overrides the day component.
        reference_date: A known past occurrence used as the interval anchor.
        cycle_start: First day of the cycle period.
        cycle_end: Last day of the cycle period (inclusive).

    Returns:
        Sorted list of occurrence dates within [cycle_start, cycle_end].
    """
    interval: int = config["interval"]
    unit: str = config["unit"]
    day_of_month: int | None = config.get("day_of_month")
    occurrences: list[date] = []

    def _step(dt: date, forward: bool) -> date:
        sign = 1 if forward else -1
        if unit == "days":
            return dt + timedelta(days=interval * sign)
        if unit == "weeks":
            return dt + timedelta(weeks=interval * sign)
        if unit == "months":
            return _add_months(dt, interval * sign)
        # years
        return _add_years(dt, interval * sign)

    def _apply_day_override(dt: date) -> date:
        if day_of_month is None:
            return dt
        max_day = calendar.monthrange(dt.year, dt.month)[1]
        return dt.replace(day=min(day_of_month, max_day))

    # Walk backward from reference_date until before cycle_start
    current = _apply_day_override(reference_date)
    while current > cycle_start:
        current = _step(current, forward=False)
        current = _apply_day_override(current)

    # Walk forward and collect dates inside the cycle window
    while current <= cycle_end:
        if current >= cycle_start:
            occurrences.append(current)
        current = _step(current, forward=True)
        current = _apply_day_override(current)

    return occurrences


def calculate_occurrences(
    recurrence_type: str,
    recurrence_config: dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date,
) -> list[date]:
    """Dispatch to the correct occurrence calculator for *recurrence_type*.

    Args:
        recurrence_type: One of ``"weekly"``, ``"bi_weekly"``, ``"monthly"``,
            ``"custom"``.
        recurrence_config: Type-specific configuration dict.
        reference_date: Known anchor date for bi_weekly / custom recurrence.
        cycle_start: First day of the cycle period.
        cycle_end: Last day of the cycle period (inclusive).

    Returns:
        Sorted list of occurrence dates within [cycle_start, cycle_end].

    Raises:
        ValueError: If *recurrence_type* is unrecognised.
    """
    if recurrence_type == "weekly":
        return calculate_weekly_occurrences(recurrence_config, cycle_start, cycle_end)
    if recurrence_type == "bi_weekly":
        return calculate_bi_weekly_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    if recurrence_type == "monthly":
        return calculate_monthly_occurrences(recurrence_config, cycle_start, cycle_end)
    if recurrence_type == "custom":
        return calculate_custom_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    raise ValueError(f"Unknown recurrence type: {recurrence_type}")
