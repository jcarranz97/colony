"""Colony MCP server — entry point.

Builds the FastMCP server, registers the curated Colony tools, and runs it
over the configured transport (streamable HTTP by default).
"""

import logging

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import settings
from .tools import register_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("colony_mcp")

mcp: FastMCP = FastMCP(
    name="Colony",
    instructions=(
        "Tools for the Colony personal expense-management app: see what is "
        "due, when the next payment is, whether expenses are on autopay, and "
        "mark expenses paid. Read tools aggregate across every household you "
        "belong to unless you pass a household name. Authentication uses a "
        "Colony personal access token, supplied by the MCP client as an "
        "'Authorization: Bearer' header."
    ),
)

register_all(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Liveness/readiness probe for container orchestration."""
    return JSONResponse({"status": "healthy", "service": "colony-mcp"})


def main() -> None:
    """Run the Colony MCP server."""
    logger.info(
        "Starting Colony MCP server on %s:%s%s (Colony API: %s)",
        settings.mcp_host,
        settings.mcp_port,
        settings.mcp_path,
        settings.colony_api_url,
    )
    mcp.run(
        transport=settings.mcp_transport,
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_path,
    )


if __name__ == "__main__":
    main()
