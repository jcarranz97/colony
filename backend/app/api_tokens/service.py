import hashlib
import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import User

from . import models
from .constants import TOKEN_DISPLAY_PREFIX_LENGTH, TOKEN_PREFIX, TOKEN_SECRET_BYTES

logger = logging.getLogger(__name__)


def _naive_utc_now() -> datetime:
    """Return the current UTC time as a naive datetime.

    The ``DateTime`` columns in this app are timezone-naive (matching
    ``BaseModel``), so all comparisons happen in naive UTC.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def _to_naive_utc(value: datetime) -> datetime:
    """Normalise a datetime to naive UTC for storage/comparison."""
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest used to store and look up a token.

    A plain SHA-256 (not a slow password hash) is appropriate here because
    the token is high-entropy random data, and a deterministic digest is
    what makes an indexed equality lookup possible.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class ApiTokenService:
    """Business logic for personal access tokens."""

    @staticmethod
    def create_token(
        db: Session,
        user: User,
        name: str,
        expires_at: datetime | None = None,
    ) -> tuple[models.ApiToken, str]:
        """Create a new personal access token.

        Args:
            db: Active database session.
            user: The owner of the new token.
            name: A user-supplied label for the token.
            expires_at: Optional expiry; ``None`` means the token never
                expires.

        Returns:
            A tuple of the persisted ``ApiToken`` and the plaintext token.
            The plaintext is shown to the user exactly once.
        """
        raw_token = f"{TOKEN_PREFIX}{secrets.token_urlsafe(TOKEN_SECRET_BYTES)}"
        token = models.ApiToken(
            user_id=user.id,
            name=name,
            token_hash=_hash_token(raw_token),
            prefix=raw_token[:TOKEN_DISPLAY_PREFIX_LENGTH],
            expires_at=_to_naive_utc(expires_at) if expires_at else None,
        )
        db.add(token)
        db.commit()
        db.refresh(token)

        logger.info(
            "API token created",
            extra={"user_id": str(user.id), "token_id": str(token.id)},
        )
        return token, raw_token

    @staticmethod
    def list_tokens(db: Session, user_id: UUID) -> list[models.ApiToken]:
        """Return all active tokens for a user, newest first."""
        return (
            db.query(models.ApiToken)
            .filter(
                models.ApiToken.user_id == user_id,
                models.ApiToken.active.is_(True),
            )
            .order_by(models.ApiToken.created_at.desc())
            .all()
        )

    @staticmethod
    def get_token_by_id(
        db: Session, token_id: UUID, user_id: UUID
    ) -> models.ApiToken | None:
        """Return an active token by ID, scoped to its owner."""
        return (
            db.query(models.ApiToken)
            .filter(
                models.ApiToken.id == token_id,
                models.ApiToken.user_id == user_id,
                models.ApiToken.active.is_(True),
            )
            .first()
        )

    @staticmethod
    def revoke_token(db: Session, token: models.ApiToken) -> None:
        """Soft-delete (revoke) an API token."""
        token.active = False
        db.commit()
        logger.info("API token revoked", extra={"token_id": str(token.id)})

    @staticmethod
    def resolve_token(db: Session, raw_token: str) -> User | None:
        """Resolve a raw personal access token to its owning user.

        Returns ``None`` when the token is unknown, revoked, expired, or
        owned by an inactive user. On a successful match, ``last_used_at``
        is updated.

        Args:
            db: Active database session.
            raw_token: The plaintext token from the ``Authorization`` header.

        Returns:
            The owning active ``User``, or ``None`` if the token is invalid.
        """
        token = (
            db.query(models.ApiToken)
            .filter(
                models.ApiToken.token_hash == _hash_token(raw_token),
                models.ApiToken.active.is_(True),
            )
            .first()
        )
        if token is None:
            return None

        now = _naive_utc_now()
        if token.expires_at is not None and token.expires_at < now:
            return None

        user = (
            db.query(User)
            .filter(User.id == token.user_id, User.active.is_(True))
            .first()
        )
        if user is None:
            return None

        token.last_used_at = now
        db.commit()
        return user


api_token_service = ApiTokenService()
