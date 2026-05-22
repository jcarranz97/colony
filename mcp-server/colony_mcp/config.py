"""Runtime configuration, sourced from environment variables."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP server settings.

    Every field can be overridden with an environment variable of the same
    name in upper case (e.g. ``COLONY_API_URL``).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base URL of the Colony REST API, including the version prefix.
    colony_api_url: str = "http://localhost:8000/api/v1"

    # Address the MCP server binds to (all interfaces, for containers).
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8002

    # FastMCP transport ("http" = streamable HTTP) and the path it serves on.
    mcp_transport: Literal["http", "streamable-http", "sse", "stdio"] = "http"
    mcp_path: str = "/mcp"

    # Timeout (seconds) for each call to the Colony API.
    colony_request_timeout: float = 30.0


settings = Settings()
