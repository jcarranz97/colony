from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.database import get_db

from . import schemas, service
from .dependencies import ApiTokenDep

router = APIRouter(prefix="/api-tokens", tags=["api-tokens"])

DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/health",
    summary="API tokens health check",
    description="Health check endpoint for the API tokens domain.",
)
async def api_token_health_check() -> dict[str, str]:
    """API tokens domain health check."""
    return {"status": "healthy", "domain": "api_tokens"}


@router.get(
    "/",
    response_model=list[schemas.ApiTokenResponse],
    summary="List personal access tokens",
    description=(
        "List the current user's personal access tokens. Only metadata is "
        "returned — the token secret is never exposed after creation."
    ),
)
async def list_api_tokens(
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> list[schemas.ApiTokenResponse]:
    """List the current user's personal access tokens."""
    tokens = service.api_token_service.list_tokens(db, current_user.id)
    return [schemas.ApiTokenResponse.model_validate(token) for token in tokens]


@router.post(
    "/",
    response_model=schemas.ApiTokenCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a personal access token",
    description=(
        "Create a personal access token for the current user. The plaintext "
        "token is included in the response exactly once and cannot be "
        "retrieved again."
    ),
)
async def create_api_token(
    payload: schemas.ApiTokenCreate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.ApiTokenCreatedResponse:
    """Create a personal access token and return the one-time secret."""
    token, raw_token = service.api_token_service.create_token(
        db, current_user, payload.name, payload.expires_at
    )
    return schemas.ApiTokenCreatedResponse(
        **schemas.ApiTokenResponse.model_validate(token).model_dump(),
        token=raw_token,
    )


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a personal access token",
    description="Revoke (soft-delete) a personal access token.",
)
async def revoke_api_token(
    api_token: ApiTokenDep,
    db: DatabaseDep,
) -> None:
    """Revoke a personal access token."""
    service.api_token_service.revoke_token(db, api_token)
