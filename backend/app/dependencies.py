"""FastAPI dependency functions for authentication and authorization."""

import os
from typing import Annotated

from fastapi import Header, HTTPException

# Get tokens from environment variables with fallback for development
VALID_X_TOKEN = os.getenv("X_TOKEN", "fake-super-secret-token")
VALID_QUERY_TOKEN = os.getenv("QUERY_TOKEN", "jessica")


async def get_token_header(x_token: Annotated[str, Header()]) -> None:
    """Validate X-Token header for API authentication.

    Args:
        x_token: Token provided in X-Token header

    Raises:
        HTTPException: If the provided token is invalid
    """
    if x_token != VALID_X_TOKEN:
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str) -> None:
    """Validate query token for API authentication.

    Args:
        token: Token provided as query parameter

    Raises:
        HTTPException: If the provided token is invalid
    """
    if token != VALID_QUERY_TOKEN:
        raise HTTPException(status_code=400, detail="No valid token provided")
