from datetime import timedelta

from fastapi import Request, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.auth.security import hash_token, new_token
from app.core.config import settings
from app.core.timezone import utcnow
from app.models import User, UserSession

# Extending on every request would write on every request; once a day is enough
REFRESH_AFTER = timedelta(days=1)


def _lifetime() -> timedelta:
    return timedelta(days=settings.session_days)


def set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=int(_lifetime().total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def start(db: Session, request: Request, response: Response, user: User) -> None:
    """Open a new login for the user and put its cookie on the response."""
    now = utcnow()
    # Opportunistic cleanup keeps the table small without a scheduler
    db.execute(delete(UserSession).where(UserSession.expires_at < now))
    token = new_token()
    db.add(
        UserSession(
            user=user,
            token_hash=hash_token(token),
            expires_at=now + _lifetime(),
            last_seen_at=now,
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
        )
    )
    db.commit()
    set_cookie(response, token)


def get_valid(db: Session, token: str) -> UserSession | None:
    return db.scalar(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.token_hash == hash_token(token), UserSession.expires_at > utcnow())
    )


def touch(db: Session, session: UserSession, token: str, response: Response) -> None:
    """Sliding expiry: a user who keeps coming back is never logged out."""
    now = utcnow()
    if now - session.last_seen_at < REFRESH_AFTER:
        return
    session.last_seen_at = now
    session.expires_at = now + _lifetime()
    db.commit()
    set_cookie(response, token)


def revoke(db: Session, session: UserSession) -> None:
    db.delete(session)
    db.commit()


def revoke_all(db: Session, user: User, keep_id: int | None = None) -> None:
    stmt = delete(UserSession).where(UserSession.user_id == user.id)
    if keep_id is not None:
        stmt = stmt.where(UserSession.id != keep_id)
    db.execute(stmt)
    db.commit()
