"""Comment tools: read and write discussion threads on Colony items.

A *comment* is a free-text Markdown note attached to any Colony item — a
cycle, a cycle expense or income, a payment method, or a recurrent
template. Comments capture context an agent or person should remember,
such as why an expense was skipped this cycle.

Comments resolve against the user's **active household**: an item in a
different household has no visible comments and cannot be commented on.
"""

from typing import Any, Literal

from fastmcp import FastMCP

from ..client import colony_request

# Colony item types a comment can be attached to. The ids for these come
# straight back from the read tools — e.g. an expense id from
# ``find_expenses`` is a ``cycle_expense``; a cycle id from ``list_cycles``
# is a ``cycle``.
CommentableEntity = Literal[
    "payment_method",
    "recurrent_expense",
    "recurrent_income",
    "cycle",
    "cycle_expense",
    "cycle_income",
]


async def add_comment(
    entity_type: CommentableEntity,
    entity_id: str,
    body: str,
) -> dict[str, Any]:
    """Add a comment to a Colony item.

    Use this to record context on any item — for example, a note on a
    cycle expense explaining why it was skipped this month. The item must
    belong to your active household.

    Args:
        entity_type: The kind of item to comment on — one of "cycle",
            "cycle_expense", "cycle_income", "payment_method",
            "recurrent_expense", or "recurrent_income".
        entity_id: UUID of the item. These ids come straight from the
            read tools — e.g. an expense id from ``find_expenses`` is a
            "cycle_expense"; a cycle id from ``list_cycles`` is a "cycle".
        body: The comment text. Markdown is supported; it cannot be empty.

    Returns:
        The created comment, including its author and timestamps.
    """
    return await colony_request(
        "POST",
        "/comments/",
        json={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "body": body,
        },
    )


async def get_comments(
    entity_type: CommentableEntity,
    entity_id: str,
) -> list[dict[str, Any]]:
    """List the comments on a single Colony item.

    Use this to pull extra context that an agent or person left on an
    item — for instance, to learn why an expense looks unusual before
    acting on it. Only items in your active household have visible
    comments.

    Args:
        entity_type: The kind of item — one of "cycle", "cycle_expense",
            "cycle_income", "payment_method", "recurrent_expense", or
            "recurrent_income".
        entity_id: UUID of the item.

    Returns:
        The item's comments, newest first.
    """
    return await colony_request(
        "GET",
        "/comments/",
        params={"entity_type": entity_type, "entity_id": entity_id},
    )


async def get_cycle_comments(cycle_id: str) -> list[dict[str, Any]]:
    """List every comment left anywhere inside a cycle.

    Returns comments on the cycle itself and on all of its expenses and
    incomes in a single call — a quick way to review the whole discussion
    around a budgeting period without querying each item.

    Args:
        cycle_id: UUID of the cycle.

    Returns:
        Comments from across the cycle, newest first.
    """
    return await colony_request(
        "GET",
        "/comments/",
        params={"cycle_id": cycle_id},
    )


def register(mcp: FastMCP) -> None:
    """Register the comment tools on the MCP server."""
    mcp.tool(add_comment)
    mcp.tool(get_comments)
    mcp.tool(get_cycle_comments)
