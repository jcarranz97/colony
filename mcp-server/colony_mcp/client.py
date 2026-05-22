"""HTTP client that forwards the caller's token to the Colony API.

The MCP server stores no credentials. On every tool call it reads the
inbound ``Authorization`` header (set by the MCP client to the user's
Colony personal access token) and replays it against the Colony REST API.
This is what keeps each user's data isolated.
"""

from typing import Any

import httpx
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from .config import settings


class ColonyAPIError(ToolError):
    """A Colony API call failed.

    Subclasses :class:`ToolError` so the message is surfaced verbatim to
    the agent rather than masked as a generic internal error.
    """


def _bearer_token() -> str:
    """Return the inbound ``Authorization`` header value.

    ``include_all=True`` is required because FastMCP strips the
    ``Authorization`` header from the default header set.

    Raises:
        ColonyAPIError: If the request carries no Authorization header.
    """
    headers = get_http_headers(include_all=True)
    auth = headers.get("authorization")
    if not auth:
        raise ColonyAPIError(
            "Not authenticated. Configure your Colony personal access token "
            "in the MCP client as an 'Authorization: Bearer colony_pat_...' "
            "header. Generate one in the Colony web app under Settings."
        )
    return auth


def _format_error(response: httpx.Response) -> str:
    """Turn a Colony JSON error envelope into a readable message."""
    try:
        payload = response.json()
    except ValueError:
        return f"Colony API error {response.status_code}: {response.text[:200]}"

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = error.get("code", "ERROR")
        message = error.get("message", "Unknown error")
        return f"Colony API error [{code}]: {message}"
    return f"Colony API error {response.status_code}"


async def colony_request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> Any:
    """Call the Colony API, forwarding the caller's bearer token.

    Args:
        method: HTTP method (GET, POST, PUT, ...).
        path: API path relative to the configured base URL, e.g. "/cycles/".
        params: Optional query parameters; keys with a ``None`` value are
            dropped.
        json: Optional JSON request body.

    Returns:
        The parsed JSON response, or ``None`` for a 204 response.

    Raises:
        ColonyAPIError: If the request is unauthenticated, the API cannot
            be reached, or it responds with an error status.
    """
    clean_params = (
        {key: value for key, value in params.items() if value is not None}
        if params
        else None
    )
    url = f"{settings.colony_api_url.rstrip('/')}{path}"
    token = _bearer_token()

    async with httpx.AsyncClient(timeout=settings.colony_request_timeout) as client:
        try:
            response = await client.request(
                method,
                url,
                params=clean_params,
                json=json,
                headers={"Authorization": token},
            )
        except httpx.HTTPError as exc:
            raise ColonyAPIError(
                f"Could not reach the Colony API at {url}: {exc}"
            ) from exc

    if response.status_code == httpx.codes.NO_CONTENT:
        return None
    if response.is_error:
        raise ColonyAPIError(_format_error(response))
    return response.json()
