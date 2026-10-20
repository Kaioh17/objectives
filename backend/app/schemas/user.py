from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, EmailStr, Field

from app.schemas.base import APIModel, TimestampSchema


def _check_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Unknown timezone, use an IANA name like Africa/Lagos") from exc
    return value


def _check_password_bytes(value: str) -> str:
    # bcrypt rejects input beyond 72 bytes, and non-ASCII characters take more than one
    if len(value.encode()) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return value


Timezone = Annotated[str, Field(max_length=64), AfterValidator(_check_timezone)]
Password = Annotated[str, Field(min_length=8), AfterValidator(_check_password_bytes)]


class UserCreate(APIModel):
    email: EmailStr
    password: Password
    full_name: str | None = Field(default=None, max_length=255)
    timezone: Timezone = "UTC"


class UserUpdate(APIModel):
    full_name: str | None = Field(default=None, max_length=255)
    timezone: Timezone | None = None
    password: Password | None = None
    # Required when the account already has a password
    current_password: str | None = None


class UserRead(TimestampSchema):
    id: int
    email: EmailStr
    full_name: str | None
    timezone: str
    is_active: bool
