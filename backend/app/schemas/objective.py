from datetime import datetime

from pydantic import AwareDatetime, Field

from app.models import Mode
from app.schemas.base import APIModel, TimestampSchema


class ObjectiveCreate(APIModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    minutes: int = Field(ge=5, le=1440)
    mode: Mode


class ObjectiveUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    minutes: int | None = Field(default=None, ge=5, le=1440)
    mode: Mode | None = None
    archived: bool | None = None


class ObjectiveRead(TimestampSchema):
    id: int
    title: str
    description: str
    minutes: int
    mode: Mode
    archived: bool
    event_id: str | None
    event_start: datetime | None
    event_end: datetime | None


class ScheduleRequest(APIModel):
    # Must carry an offset (2026-11-02T09:00:00+01:00 or ...Z); stored as UTC
    start: AwareDatetime
    # Defaults to the objective's own length
    minutes: int | None = Field(default=None, ge=5, le=1440)
