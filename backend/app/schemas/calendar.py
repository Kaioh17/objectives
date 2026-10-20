from datetime import datetime

from app.schemas.base import APIModel


class CalendarStatus(APIModel):
    connected: bool
    email: str | None = None


class ScheduleItem(APIModel):
    id: str
    title: str
    start: datetime
    end: datetime
