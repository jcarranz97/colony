"""Activity tools: read the change history of Colony items.

Activity is the audit log that runs alongside [[comments]]: every time a
field on an item is changed (due date moved, status flipped to paid,
amount edited, an item created or deactivated), a row is appended with
who did it, when, and which fields shifted. Comments are what users
*wrote*; activity is what users *did*.

Reach for these tools when the user asks things like "what changed on
this expense?", "who moved the due date?", "when did this become paid?".
A plain ``updated_at`` timestamp on the item only reflects the last
mutation — to answer change-history questions you need the activity log.

Activity resolves against the user's **active household**: items in a
different household have no visible activity.
"""

from typing import Any

from fastmcp import FastMCP

from ..client import colony_request
from .comments import CommentableEntity


async def get_activity(
    entity_type: CommentableEntity,
    entity_id: str,
) -> list[dict[str, Any]]:
    """List the change history of a single Colony item.

    Each row records one mutation: who made it, when, the action
    (``created``, ``updated``, ``marked_paid``, ``status_changed``,
    ``deactivated``, ``completed``, …) and a ``changes`` dict with the
    field-level diff. For example, moving an expense's due date yields a
    row like ``changes = {"due_date": {"from": "2026-05-16", "to":
    "2026-05-26"}}``. Use this — not the item's ``updated_at`` field —
    whenever the user asks what changed, who changed it, or when.

    Args:
        entity_type: The kind of item — one of "cycle", "cycle_expense",
            "cycle_income", "payment_method", "recurrent_expense", or
            "recurrent_income".
        entity_id: UUID of the item. These ids come straight from the
            read tools — e.g. an expense id from ``find_expenses`` is a
            "cycle_expense"; a cycle id from ``list_cycles`` is a "cycle".

    Returns:
        Activity rows for the item, newest first.
    """
    return await colony_request(
        "GET",
        "/activity/",
        params={"entity_type": entity_type, "entity_id": entity_id},
    )


async def get_cycle_activity(cycle_id: str) -> list[dict[str, Any]]:
    """List every activity row recorded anywhere inside a cycle.

    Returns activity for the cycle itself and for all of its expenses
    and incomes in a single call — a quick way to audit who did what
    across a whole budgeting period without querying each item.

    Args:
        cycle_id: UUID of the cycle.

    Returns:
        Activity rows from across the cycle, newest first.
    """
    return await colony_request(
        "GET",
        "/activity/",
        params={"cycle_id": cycle_id},
    )


def register(mcp: FastMCP) -> None:
    """Register the activity tools on the MCP server."""
    mcp.tool(get_activity)
    mcp.tool(get_cycle_activity)
