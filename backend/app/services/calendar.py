from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import decrypt_secret, encrypt_secret
from app.core.exceptions import ConflictError
from app.core.timezone import day_bounds_utc, get_zone, utcnow
from app.models import GoogleAccount, Objective, User
from app.schemas import CalendarStatus, ScheduleItem, ScheduleRequest
from app.services import google

# Refresh a little early so a token never expires mid-request
EXPIRY_MARGIN = timedelta(seconds=60)


def get_account(db: Session, user: User) -> GoogleAccount | None:
    return db.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))


def _connected(account: GoogleAccount | None) -> bool:
    return bool(
        account and account.refresh_token and google.CALENDAR_SCOPE in account.scopes.split()
    )


def status(db: Session, user: User) -> CalendarStatus:
    account = get_account(db, user)
    return CalendarStatus(connected=_connected(account), email=account.email if account else None)


def _access_token(db: Session, user: User) -> str:
    account = get_account(db, user)
    if account is None or not _connected(account):
        raise ConflictError("Google Calendar is not connected")

    cached = decrypt_secret(account.access_token) if account.access_token else None
    expires = account.access_token_expires_at
    if cached and expires and expires - utcnow() > EXPIRY_MARGIN:
        return cached

    refresh_token = decrypt_secret(account.refresh_token or "")
    if refresh_token is None:
        raise ConflictError("Google Calendar access expired, connect Google again")
    try:
        tokens = google.refresh_access_token(refresh_token)
    except ConflictError:
        # The refresh token is dead; forget it so status() reports disconnected
        account.refresh_token = account.access_token = None
        db.commit()
        raise
    account.access_token = encrypt_secret(tokens["access_token"])
    account.access_token_expires_at = utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    db.commit()
    return tokens["access_token"]


def disconnect(db: Session, user: User) -> None:
    account = get_account(db, user)
    if account is None:
        return
    if account.refresh_token and (token := decrypt_secret(account.refresh_token)):
        google.revoke(token)
    db.delete(account)
    db.commit()


def list_day(db: Session, user: User, day: date) -> list[ScheduleItem]:
    """The user's events for a calendar day in the user's own timezone."""
    start, end = day_bounds_utc(day, user.timezone)
    zone = get_zone(user.timezone)
    items: list[ScheduleItem] = []
    for event in google.list_events(_access_token(db, user), start, end):
        s, e = event["start"], event["end"]
        if "dateTime" in s:
            begin, finish = (
                datetime.fromisoformat(s["dateTime"]),
                datetime.fromisoformat(e["dateTime"]),
            )
        else:
            # All-day events carry a bare date: span the day in the user's zone
            begin = datetime.fromisoformat(s["date"]).replace(tzinfo=zone)
            finish = datetime.fromisoformat(e["date"]).replace(tzinfo=zone)
        items.append(
            ScheduleItem(
                id=event["id"], title=event.get("summary") or "(No title)", start=begin, end=finish
            )
        )
    return items


def schedule(db: Session, user: User, objective: Objective, data: ScheduleRequest) -> Objective:
    """Create the Google event for an objective, or move it if one already exists."""
    token = _access_token(db, user)
    minutes = data.minutes or objective.minutes
    start = data.start
    end = start + timedelta(minutes=minutes)
    body = google.event_body(objective.title, objective.description, start, end, user.timezone)

    event_id = google.patch_event(token, objective.event_id, body) if objective.event_id else None
    objective.event_id = event_id or google.insert_event(token, body)
    objective.event_start = start
    objective.event_end = end
    db.commit()
    db.refresh(objective)
    return objective


def remove_event(db: Session, user: User, objective: Objective) -> None:
    if objective.event_id:
        google.delete_event(_access_token(db, user), objective.event_id)
    objective.event_id = objective.event_start = objective.event_end = None


def unschedule(db: Session, user: User, objective: Objective) -> Objective:
    remove_event(db, user, objective)
    db.commit()
    db.refresh(objective)
    return objective
