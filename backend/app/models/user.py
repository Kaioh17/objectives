from typing import TYPE_CHECKING

from sqlalchemy import String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.google_account import GoogleAccount
    from app.models.objective import Objective


class User(TimestampMixin, Base):
    """Single role: everyone is a regular user. The admin works in the database console."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored lowercase; the unique constraint also backs the login lookup
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    # Null for accounts that only ever signed in with Google
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    # IANA name; every timestamp is stored in UTC and converted to this zone in code
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    # Embedded in every JWT; bumping it signs the user out everywhere
    token_version: Mapped[int] = mapped_column(default=0, server_default="0")

    google_account: Mapped["GoogleAccount | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    objectives: Mapped[list["Objective"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
