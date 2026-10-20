"""Thin client for Google OAuth and the Calendar REST API (plain HTTPX, no Google SDK)."""

import logging
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import AppError, BadGatewayError, ConflictError
from app.core.timezone import utcnow

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"
SCOPES = ["openid", "email", "profile", CALENDAR_SCOPE]

STATE_ALGORITHM = "HS256"
STATE_TTL = timedelta(minutes=10)


def _send(method: str, url: str, **kwargs: Any) -> httpx.Response:
    try:
        with httpx.Client(timeout=10.0) as client:
            return client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        logger.warning("Google request failed: %s %s (%s)", method, url, exc)
        raise BadGatewayError("Could not reach Google") from exc


def require_configured() -> None:
    if not settings.google_enabled:
        raise AppError("Google sign-in is not configured on this server")


# --- OAuth ---------------------------------------------------------------------------------


def make_state(nonce: str, next_path: str) -> str:
    """Signed state; the nonce also sits in a cookie, tying the callback to this browser."""
    payload = {"nonce": nonce, "next": next_path, "exp": utcnow() + STATE_TTL}
    return jwt.encode(payload, settings.secret_key, algorithm=STATE_ALGORITHM)


def read_state(state: str) -> dict[str, str] | None:
    try:
        return jwt.decode(state, settings.secret_key, algorithms=[STATE_ALGORITHM])
    except jwt.PyJWTError:
        return None


def authorization_url(state: str, login_hint: str | None = None) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        # offline + consent: Google only returns a refresh token when both are set
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    if login_hint:
        params["login_hint"] = login_hint
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict[str, Any]:
    res = _send(
        "POST",
        TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    if res.status_code != 200:
        logger.warning("Google code exchange failed: %s %s", res.status_code, res.text)
        raise BadGatewayError("Google rejected the sign-in")
    return res.json()


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    res = _send(
        "POST",
        TOKEN_URL,
        data={
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        },
    )
    if res.status_code == 400 and res.json().get("error") == "invalid_grant":
        # Revoked in the Google account page, or expired (7 days while the app is in Testing)
        raise ConflictError("Google Calendar access expired, connect Google again")
    if res.status_code != 200:
        logger.warning("Google token refresh failed: %s %s", res.status_code, res.text)
        raise BadGatewayError("Could not refresh Google access")
    return res.json()


def userinfo(access_token: str) -> dict[str, Any]:
    res = _send("GET", USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    if res.status_code != 200:
        raise BadGatewayError("Could not read the Google profile")
    return res.json()


def revoke(token: str) -> None:
    """Best effort: the local link is removed even if Google is unreachable."""
    try:
        _send("POST", REVOKE_URL, data={"token": token})
    except BadGatewayError:
        pass


# --- Calendar ------------------------------------------------------------------------------


def _calendar(method: str, url: str, access_token: str, **kwargs: Any) -> httpx.Response:
    res = _send(method, url, headers={"Authorization": f"Bearer {access_token}"}, **kwargs)
    if res.status_code in (401, 403):
        raise ConflictError("Google Calendar access was denied, connect Google again")
    return res


def _check(res: httpx.Response, ok: tuple[int, ...] = (200,)) -> httpx.Response:
    if res.status_code not in ok:
        logger.warning("Google Calendar error: %s %s", res.status_code, res.text)
        raise BadGatewayError("Google Calendar request failed")
    return res


def list_events(access_token: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    res = _calendar(
        "GET",
        EVENTS_URL,
        access_token,
        params={
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 50,
        },
    )
    return _check(res).json().get("items", [])


def event_body(
    title: str, description: str, start: datetime, end: datetime, zone: str
) -> dict[str, Any]:
    return {
        "summary": title,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": zone},
        "end": {"dateTime": end.isoformat(), "timeZone": zone},
    }


def insert_event(access_token: str, body: dict[str, Any]) -> str:
    return _check(_calendar("POST", EVENTS_URL, access_token, json=body)).json()["id"]


def patch_event(access_token: str, event_id: str, body: dict[str, Any]) -> str | None:
    """Returns the event id, or None when the event no longer exists in Google."""
    res = _calendar("PATCH", f"{EVENTS_URL}/{event_id}", access_token, json=body)
    if res.status_code in (404, 410):
        return None
    return _check(res).json()["id"]


def delete_event(access_token: str, event_id: str) -> None:
    res = _calendar("DELETE", f"{EVENTS_URL}/{event_id}", access_token)
    _check(res, ok=(200, 204, 404, 410))
