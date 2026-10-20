from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime

if TYPE_CHECKING:
    from app.models.user import User


class UserSession(TimestampMixin, Base):
    """Long-lived login. The cookie holds a random token; only its SHA-256 is stored."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # Indexed for the cleanup of expired rows
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
    user_agent: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="sessions")
