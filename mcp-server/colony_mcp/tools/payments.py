"""Payment-method and recurrent-template tools (read-only).

Recurrent expenses and incomes are listed for context, but this server
deliberately exposes no tools to create, edit, or delete them.
"""

from typing import Any

from fastmcp import FastMCP

from ..client import colony_request
from ..households import households_to_query


async def list_payment_methods(household: str | None = None) -> list[dict[str, Any]]:
    """List payment methods (cards, cash, transfers), across households.

    Args:
        household: Optional household name to narrow to. Omit to cover all.

    Returns:
        Payment methods, each annotated with a ``household`` name.
    """
    results: list[dict[str, Any]] = []
    for household_id, household_name in await households_to_query(household):
        methods = await colony_request(
            "GET",
            "/payment-methods/",
            params={"household_id": household_id},
        )
        for method in methods:
            method["household"] = household_name
            results.append(method)
    return results


async def recurrent_expenses_overview(
    household: str | None = None,
) -> list[dict[str, Any]]:
    """List recurrent expense templates (read-only), across households.

    These templates define repeating bills and their schedules. This
    server cannot modify them — use the Colony web app for that.

    Args:
        household: Optional household name to narrow to. Omit to cover all.
    """
    results: list[dict[str, Any]] = []
    for household_id, household_name in await households_to_query(household):
        templates = await colony_request(
            "GET",
            "/recurrent-expenses/",
            params={"household_id": household_id},
        )
        for template in templates:
            template["household"] = household_name
            results.append(template)
    return results


async def recurrent_incomes_overview(
    household: str | None = None,
) -> list[dict[str, Any]]:
    """List recurrent income templates (read-only), across households.

    Args:
        household: Optional household name to narrow to. Omit to cover all.
    """
    results: list[dict[str, Any]] = []
    for household_id, household_name in await households_to_query(household):
        templates = await colony_request(
            "GET",
            "/recurrent-incomes/",
            params={"household_id": household_id},
        )
        for template in templates:
            template["household"] = household_name
            results.append(template)
    return results


def register(mcp: FastMCP) -> None:
    """Register the payment and recurrent-template tools on the MCP server."""
    mcp.tool(list_payment_methods)
    mcp.tool(recurrent_expenses_overview)
    mcp.tool(recurrent_incomes_overview)
