from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime

if TYPE_CHECKING:
    from app.models.user import User


class GoogleAccount(TimestampMixin, Base):
    """The Google identity linked to a user, plus the tokens for their Calendar."""

    __tablename__ = "google_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # One Google account per user; the unique constraint also indexes the FK
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    google_sub: Mapped[str] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(255))
    # Both tokens are Fernet-encrypted, never stored in plain text
    refresh_token: Mapped[str | None] = mapped_column(Text)
    access_token: Mapped[str | None] = mapped_column(Text)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    # Space-separated scopes the user actually granted
    scopes: Mapped[str] = mapped_column(Text, default="")

    user: Mapped["User"] = relationship(back_populates="google_account")
