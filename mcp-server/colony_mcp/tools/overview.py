"""Account- and household-level tools."""

from typing import Any

from fastmcp import FastMCP

from ..client import colony_request


async def whoami() -> dict[str, Any]:
    """Identify the Colony account this session is acting as.

    Returns the current user's profile (username, name, preferred
    currency, role). Useful for confirming whose data the agent can see.
    """
    return await colony_request("GET", "/auth/me")


async def list_households() -> list[dict[str, Any]]:
    """List every household the current user belongs to.

    Most read tools aggregate across all of these by default. Pass a
    household name to a tool to narrow its scope to one household.
    """
    return await colony_request("GET", "/households/me")


def register(mcp: FastMCP) -> None:
    """Register the overview tools on the MCP server."""
    mcp.tool(whoami)
    mcp.tool(list_households)
