"""Cycle tools: cycles, summaries, and incomes.

A *cycle* is a budgeting period (typically a month) holding expenses and
incomes. Read tools aggregate across households unless a household name is
given; cycle-scoped tools resolve the household from the cycle id.
"""

from datetime import date
from typing import Any

from fastmcp import FastMCP

from ..client import ColonyAPIError, colony_request
from ..households import (
    households_to_query,
    resolve_cycle_household_id,
    resolve_target_household,
)


async def list_cycles(
    household: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List budgeting cycles, aggregated across households.

    Args:
        household: Optional household name to narrow to. When omitted,
            cycles from every household the user belongs to are returned.
        status: Optional status filter — "draft", "active", or "completed".

    Returns:
        Cycles, each annotated with a ``household`` name.
    """
    results: list[dict[str, Any]] = []
    for household_id, household_name in await households_to_query(household):
        payload = await colony_request(
            "GET",
            "/cycles/",
            params={
                "household_id": household_id,
                "status": status,
                "per_page": 100,
            },
        )
        for cycle in payload["cycles"]:
            cycle["household"] = household_name
            results.append(cycle)
    return results


async def get_current_cycle(household: str | None = None) -> list[dict[str, Any]]:
    """Return the open cycle(s) whose date range includes today.

    This is the cycle "this week" or "this month" lives in. Both active and
    draft cycles count — a draft cycle covering today is still your current
    cycle; only completed cycles are excluded.

    Args:
        household: Optional household name to narrow to.

    Returns:
        Open (active or draft) cycles covering today's date, one per
        household that has one.
    """
    today = date.today().isoformat()
    return [
        cycle
        for cycle in await list_cycles(household=household)
        if cycle["status"] != "completed"
        and cycle["start_date"] <= today <= cycle["end_date"]
    ]


async def create_cycle(
    name: str,
    start_date: str,
    end_date: str,
    household: str | None = None,
    generate_from_templates: bool = False,
) -> dict[str, Any]:
    """Create a new budgeting cycle.

    A cycle is a budgeting period (typically a month) that expenses and
    incomes are recorded against. The end date must be after the start
    date, and the name must be unique within its household. A new cycle
    starts in "draft" status.

    Args:
        name: Name for the cycle, e.g. "May-June 2026 Cycle".
        start_date: First day the cycle covers (YYYY-MM-DD).
        end_date: Last day the cycle covers (YYYY-MM-DD); must be after
            ``start_date``.
        household: Optional household name to create the cycle in. Required
            only when you belong to more than one household.
        generate_from_templates: When true, the cycle is pre-populated with
            expenses generated from every active recurrent template.

    Returns:
        The newly created cycle.
    """
    household_id, _ = await resolve_target_household(household)
    return await colony_request(
        "POST",
        "/cycles/",
        params={"household_id": household_id},
        json={
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "generate_from_templates": generate_from_templates,
        },
    )


async def get_cycle_summary(cycle_id: str) -> dict[str, Any]:
    """Return a cycle's financial summary.

    Includes totals by category, by payment method, by currency, and a
    breakdown of expense statuses (paid, pending, overdue, ...).

    Args:
        cycle_id: UUID of the cycle.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    return await colony_request(
        "GET",
        f"/cycles/{cycle_id}/summary",
        params={"household_id": household_id},
    )


async def list_cycle_incomes(cycle_id: str) -> list[dict[str, Any]]:
    """List every income recorded in a cycle.

    Args:
        cycle_id: UUID of the cycle.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    return await colony_request(
        "GET",
        f"/cycles/{cycle_id}/incomes",
        params={"household_id": household_id},
    )


async def add_cycle_income(
    cycle_id: str,
    description: str,
    amount: float,
    currency: str,
    income_date: str,
    payment_method_id: str | None = None,
    comments: str | None = None,
) -> dict[str, Any]:
    """Record a new income in a cycle.

    Args:
        cycle_id: UUID of the cycle to add the income to.
        description: What the income is for.
        amount: Income amount in its native currency.
        currency: Currency code — "USD" or "MXN".
        income_date: Date the income was received (YYYY-MM-DD).
        payment_method_id: Optional UUID of the payment method it landed in.
        comments: Optional free-text note.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    body: dict[str, Any] = {
        "description": description,
        "amount": amount,
        "currency": currency,
        "income_date": income_date,
    }
    if payment_method_id is not None:
        body["payment_method_id"] = payment_method_id
    if comments is not None:
        body["comments"] = comments
    return await colony_request(
        "POST",
        f"/cycles/{cycle_id}/incomes",
        params={"household_id": household_id},
        json=body,
    )


async def update_cycle_income(
    cycle_id: str,
    income_id: str,
    description: str | None = None,
    amount: float | None = None,
    income_date: str | None = None,
    comments: str | None = None,
) -> dict[str, Any]:
    """Update fields on an existing cycle income.

    Only the arguments you provide are changed.

    Args:
        cycle_id: UUID of the cycle containing the income.
        income_id: UUID of the income to update.
        description: New description, if changing it.
        amount: New amount, if changing it.
        income_date: New income date (YYYY-MM-DD), if changing it.
        comments: New comment text, if changing it.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    body = {
        key: value
        for key, value in {
            "description": description,
            "amount": amount,
            "income_date": income_date,
            "comments": comments,
        }.items()
        if value is not None
    }
    if not body:
        raise ColonyAPIError("Provide at least one field to update.")
    return await colony_request(
        "PUT",
        f"/cycles/{cycle_id}/incomes/{income_id}",
        params={"household_id": household_id},
        json=body,
    )


def register(mcp: FastMCP) -> None:
    """Register the cycle tools on the MCP server."""
    mcp.tool(list_cycles)
    mcp.tool(get_current_cycle)
    mcp.tool(create_cycle)
    mcp.tool(get_cycle_summary)
    mcp.tool(list_cycle_incomes)
    mcp.tool(add_cycle_income)
    mcp.tool(update_cycle_income)
