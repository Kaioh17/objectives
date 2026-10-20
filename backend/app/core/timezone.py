from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Storage and the API speak UTC. Convert to the user's zone only where the calendar day matters.


def utcnow() -> datetime:
    return datetime.now(UTC)


def get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def to_zone(value: datetime, name: str) -> datetime:
    return value.astimezone(get_zone(name))


def day_bounds_utc(day: date, zone_name: str) -> tuple[datetime, datetime]:
    """UTC start and end of a calendar day as the user lives it."""
    zone = get_zone(zone_name)
    start = datetime.combine(day, time.min, tzinfo=zone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)
