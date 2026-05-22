"""Expense tools: what is due, what is overdue, and safe mutations.

Read tools aggregate across every household the user belongs to (unless a
household name is given) by scanning every *open* cycle — active or draft —
of each household. Completed cycles are treated as historical and skipped.
Write tools are limited to cycle expenses — recurrent-expense templates
are intentionally read-only through this server.
"""

from datetime import date, timedelta
from typing import Any

from fastmcp import FastMCP

from ..client import ColonyAPIError, colony_request
from ..households import (
    households_to_query,
    resolve_cycle_household_id,
    resolve_expense_location,
)

# Expense statuses that represent money the user still owes.
_UNPAID_STATUSES = {"pending", "overdue"}

# Cycle statuses whose expenses are still "live". Drafts are included so the
# current cycle is visible before it is formally activated; only completed
# cycles are excluded as historical.
_OPEN_CYCLE_STATUSES = {"active", "draft"}


async def _open_cycle_expenses(household: str | None) -> list[dict[str, Any]]:
    """Collect expenses from every open cycle, annotated with context.

    An *open* cycle is one that is active or draft; completed cycles are
    skipped. Each expense gains ``household``, ``cycle_id``, and
    ``cycle_name`` keys so aggregated results stay traceable.
    """
    expenses: list[dict[str, Any]] = []
    for household_id, household_name in await households_to_query(household):
        cycles = await colony_request(
            "GET",
            "/cycles/",
            params={
                "household_id": household_id,
                "per_page": 100,
            },
        )
        for cycle in cycles["cycles"]:
            if cycle["status"] not in _OPEN_CYCLE_STATUSES:
                continue
            payload = await colony_request(
                "GET",
                f"/cycles/{cycle['id']}/expenses",
                params={"household_id": household_id},
            )
            for expense in payload["expenses"]:
                expense["household"] = household_name
                expense["cycle_id"] = cycle["id"]
                expense["cycle_name"] = cycle["name"]
                expenses.append(expense)
    return expenses


async def list_cycle_expenses(
    cycle_id: str,
    status: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """List the expenses of a specific cycle, with a totals summary.

    Args:
        cycle_id: UUID of the cycle.
        status: Optional status filter (pending, paid, overdue, ...).
        category: Optional category filter (fixed, variable, extra).
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    return await colony_request(
        "GET",
        f"/cycles/{cycle_id}/expenses",
        params={
            "household_id": household_id,
            "status": status,
            "category": category,
        },
    )


async def find_expenses(
    query: str,
    household: str | None = None,
    include_paid: bool = False,
) -> list[dict[str, Any]]:
    """Find expenses across open cycles by description.

    Case-insensitive substring match on the expense description — use it to
    locate an expense by name (e.g. "apples") without listing a whole
    cycle. Each result carries ``cycle_id`` and ``household`` for follow-up
    calls such as ``mark_expense_paid``.

    Args:
        query: Text to look for in the expense description.
        household: Optional household name to narrow to. Omit to cover all.
        include_paid: When False (default), only unpaid (pending/overdue)
            expenses are returned.

    Returns:
        Matching expenses sorted by due date (soonest first).
    """
    needle = query.strip().lower()
    matches = [
        expense
        for expense in await _open_cycle_expenses(household)
        if needle in expense["description"].lower()
        and (include_paid or expense["status"] in _UNPAID_STATUSES)
    ]
    return sorted(matches, key=lambda expense: expense["due_date"])


async def expenses_due_this_week(household: str | None = None) -> list[dict[str, Any]]:
    """List unpaid expenses due within the next 7 days.

    Args:
        household: Optional household name to narrow to. Omit to cover all.

    Returns:
        Unpaid (pending/overdue) expenses from active cycles whose due date
        falls between today and 7 days from now.
    """
    return await upcoming_expenses(days=7, household=household)


async def upcoming_expenses(
    days: int = 14,
    household: str | None = None,
) -> list[dict[str, Any]]:
    """List unpaid expenses due within the next ``days`` days.

    Args:
        days: Size of the look-ahead window, in days.
        household: Optional household name to narrow to. Omit to cover all.

    Returns:
        Matching expenses sorted by due date (soonest first).
    """
    today = date.today()
    horizon = (today + timedelta(days=days)).isoformat()
    today_iso = today.isoformat()
    due = [
        expense
        for expense in await _open_cycle_expenses(household)
        if expense["status"] in _UNPAID_STATUSES
        and today_iso <= expense["due_date"] <= horizon
    ]
    return sorted(due, key=lambda expense: expense["due_date"])


async def overdue_expenses(household: str | None = None) -> list[dict[str, Any]]:
    """List expenses that are past due and still unpaid.

    Args:
        household: Optional household name to narrow to. Omit to cover all.
    """
    overdue = [
        expense
        for expense in await _open_cycle_expenses(household)
        if expense["status"] == "overdue"
    ]
    return sorted(overdue, key=lambda expense: expense["due_date"])


async def next_payment(household: str | None = None) -> dict[str, Any]:
    """Return the single soonest unpaid expense.

    Args:
        household: Optional household name to narrow to. Omit to cover all.

    Returns:
        The unpaid expense with the earliest due date, or a message when
        there are none.
    """
    unpaid = [
        expense
        for expense in await _open_cycle_expenses(household)
        if expense["status"] in _UNPAID_STATUSES
    ]
    if not unpaid:
        return {"message": "No upcoming unpaid expenses found."}
    return min(unpaid, key=lambda expense: expense["due_date"])


async def list_autopay_expenses(household: str | None = None) -> list[dict[str, Any]]:
    """List expenses set to pay automatically (autopay enabled).

    Answers questions like "is my electricity bill on autopay?".

    Args:
        household: Optional household name to narrow to. Omit to cover all.
    """
    return [
        expense
        for expense in await _open_cycle_expenses(household)
        if expense.get("autopay")
    ]


async def mark_expense_paid(
    expense_id: str,
    cycle_id: str | None = None,
) -> dict[str, Any]:
    """Mark a single cycle expense as paid.

    Sets the expense's status to "paid" and records the payment timestamp.
    To settle several expenses at once, use ``mark_cycle_expenses_paid``.

    Args:
        expense_id: UUID of the expense to mark paid.
        cycle_id: UUID of the cycle containing the expense. Optional — when
            omitted it is resolved by scanning your open cycles, which costs
            extra requests, so pass it whenever you already know it.
    """
    if cycle_id is None:
        cycle_id, household_id = await resolve_expense_location(expense_id)
    else:
        household_id = await resolve_cycle_household_id(cycle_id)
    return await colony_request(
        "PUT",
        f"/cycles/{cycle_id}/expenses/{expense_id}",
        params={"household_id": household_id},
        json={"paid": True},
    )


async def mark_cycle_expenses_paid(
    cycle_id: str,
    expense_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Mark several expenses in one cycle as paid in a single call.

    Use this instead of repeated ``mark_expense_paid`` calls when settling
    a whole cycle at once.

    Args:
        cycle_id: UUID of the cycle.
        expense_ids: Explicit UUIDs to mark paid. When omitted, every
            still-unpaid (pending or overdue) expense in the cycle is
            marked paid.

    Returns:
        A summary with the number of expenses marked and their updated
        records.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    if expense_ids is None:
        payload = await colony_request(
            "GET",
            f"/cycles/{cycle_id}/expenses",
            params={"household_id": household_id},
        )
        expense_ids = [
            str(expense["id"])
            for expense in payload["expenses"]
            if expense["status"] in _UNPAID_STATUSES
        ]
    marked: list[dict[str, Any]] = []
    for expense_id in expense_ids:
        updated = await colony_request(
            "PUT",
            f"/cycles/{cycle_id}/expenses/{expense_id}",
            params={"household_id": household_id},
            json={"paid": True},
        )
        marked.append(updated)
    return {
        "cycle_id": cycle_id,
        "marked_count": len(marked),
        "expenses": marked,
    }


async def add_cycle_expense(
    cycle_id: str,
    description: str,
    amount: float,
    currency: str,
    payment_method_id: str,
    due_date: str,
    category: str,
    comments: str | None = None,
    autopay: bool = False,
) -> dict[str, Any]:
    """Add a new expense to a cycle.

    Args:
        cycle_id: UUID of the cycle to add the expense to.
        description: What the expense is for.
        amount: Expense amount in its native currency.
        currency: Currency code — "USD" or "MXN".
        payment_method_id: UUID of the payment method (see
            ``list_payment_methods``).
        due_date: When the expense is due (YYYY-MM-DD).
        category: Expense category — "fixed", "variable", or "extra".
        comments: Optional free-text note.
        autopay: Whether the expense pays automatically.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    body: dict[str, Any] = {
        "description": description,
        "amount": amount,
        "currency": currency,
        "payment_method_id": payment_method_id,
        "due_date": due_date,
        "category": category,
        "autopay": autopay,
    }
    if comments is not None:
        body["comments"] = comments
    return await colony_request(
        "POST",
        f"/cycles/{cycle_id}/expenses",
        params={"household_id": household_id},
        json=body,
    )


async def update_cycle_expense(
    cycle_id: str,
    expense_id: str,
    description: str | None = None,
    amount: float | None = None,
    due_date: str | None = None,
    category: str | None = None,
    comments: str | None = None,
    paid: bool | None = None,
) -> dict[str, Any]:
    """Update fields on an existing cycle expense.

    Only the arguments you provide are changed. Setting ``paid`` to true
    also marks the expense paid.

    Args:
        cycle_id: UUID of the cycle containing the expense.
        expense_id: UUID of the expense to update.
        description: New description, if changing it.
        amount: New amount, if changing it.
        due_date: New due date (YYYY-MM-DD), if changing it.
        category: New category (fixed/variable/extra), if changing it.
        comments: New comment text, if changing it.
        paid: New paid flag, if changing it.
    """
    household_id = await resolve_cycle_household_id(cycle_id)
    body = {
        key: value
        for key, value in {
            "description": description,
            "amount": amount,
            "due_date": due_date,
            "category": category,
            "comments": comments,
            "paid": paid,
        }.items()
        if value is not None
    }
    if not body:
        raise ColonyAPIError("Provide at least one field to update.")
    return await colony_request(
        "PUT",
        f"/cycles/{cycle_id}/expenses/{expense_id}",
        params={"household_id": household_id},
        json=body,
    )


def register(mcp: FastMCP) -> None:
    """Register the expense tools on the MCP server."""
    mcp.tool(list_cycle_expenses)
    mcp.tool(find_expenses)
    mcp.tool(expenses_due_this_week)
    mcp.tool(upcoming_expenses)
    mcp.tool(overdue_expenses)
    mcp.tool(next_payment)
    mcp.tool(list_autopay_expenses)
    mcp.tool(mark_expense_paid)
    mcp.tool(mark_cycle_expenses_paid)
    mcp.tool(add_cycle_expense)
    mcp.tool(update_cycle_expense)
