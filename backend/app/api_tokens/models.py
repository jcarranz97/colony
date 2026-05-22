import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel


class ApiToken(BaseModel):
    """A personal access token a user uses to authenticate API clients.

    Only the SHA-256 hash of the token is stored — the plaintext is shown
    to the user once at creation time and is never recoverable afterwards.
    """

    __tablename__ = "api_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    prefix: Mapped[str] = mapped_column(String(24), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        """String representation of ApiToken."""
        return f"<ApiToken(id={self.id}, name='{self.name}')>"
