"""Tool registration for the Colony MCP server."""

from fastmcp import FastMCP

from . import cycles, expenses, overview, payments


def register_all(mcp: FastMCP) -> None:
    """Register every Colony tool group on the MCP server."""
    overview.register(mcp)
    cycles.register(mcp)
    expenses.register(mcp)
    payments.register(mcp)
