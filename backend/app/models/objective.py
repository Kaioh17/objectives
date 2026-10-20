import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime

if TYPE_CHECKING:
    from app.models.user import User


class Mode(enum.StrEnum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class Objective(TimestampMixin, Base):
    __tablename__ = "objectives"
    __table_args__ = (
        # Serves the board query: one user's objectives, newest first
        Index("ix_objectives_user_id_created_at", "user_id", "created_at"),
        CheckConstraint("minutes BETWEEN 5 AND 1440", name="minutes_range"),
        CheckConstraint("mode IN ('daily', 'weekly', 'monthly')", name="mode_valid"),
        # The three event columns are set together or not at all
        CheckConstraint(
            "(event_id IS NULL) = (event_start IS NULL)"
            " AND (event_id IS NULL) = (event_end IS NULL)",
            name="event_all_or_none",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500), default="", server_default="")
    minutes: Mapped[int]
    # Stored as text plus a CHECK, not a native enum: adding a mode later is a plain migration
    mode: Mapped[Mode] = mapped_column(Enum(Mode, native_enum=False, length=16))
    archived: Mapped[bool] = mapped_column(default=False, server_default=false())

    # The Google Calendar event this objective is scheduled as
    event_id: Mapped[str | None] = mapped_column(String(255))
    event_start: Mapped[datetime | None] = mapped_column(UTCDateTime)
    event_end: Mapped[datetime | None] = mapped_column(UTCDateTime)

    user: Mapped["User"] = relationship(back_populates="objectives")
