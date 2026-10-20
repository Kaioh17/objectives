from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select

from app.models import GoogleAccount, User
from app.services import google
from tests.conftest import CREDS

API = "/api/v1"
SCOPE = "openid email profile " + google.CALENDAR_SCOPE
NEW = {"title": "Deep work", "description": "No phone", "minutes": 45, "mode": "daily"}


class FakeGoogle:
    """Replaces the HTTP layer so no test touches the network."""

    def __init__(self):
        self.profile = {
            "sub": "sub-1",
            "email": "g@example.com",
            "email_verified": True,
            "name": "G",
        }
        self.events: dict[str, dict] = {}
        self.calls: list[str] = []
        self.refreshes = 0

    def exchange_code(self, code):
        return {
            "access_token": "access-1",
            "refresh_token": "refresh-1",
            "expires_in": 3600,
            "scope": SCOPE,
        }

    def userinfo(self, access_token):
        return self.profile

    def refresh_access_token(self, refresh_token):
        self.refreshes += 1
        return {"access_token": f"access-r{self.refreshes}", "expires_in": 3600}

    def revoke(self, token):
        self.calls.append("revoke")

    def list_events(self, token, start, end):
        return [
            {
                "id": "e1",
                "summary": "Standup",
                "start": {"dateTime": "2026-11-02T09:30:00+01:00"},
                "end": {"dateTime": "2026-11-02T10:00:00+01:00"},
            },
            {"id": "e2", "start": {"date": "2026-11-02"}, "end": {"date": "2026-11-03"}},
        ]

    def insert_event(self, token, body):
        event_id = f"ev{len(self.events) + 1}"
        self.events[event_id] = body
        return event_id

    def patch_event(self, token, event_id, body):
        if event_id not in self.events:
            return None
        self.events[event_id] = body
        return event_id

    def delete_event(self, token, event_id):
        self.events.pop(event_id, None)


@pytest.fixture
def fake(monkeypatch):
    fake = FakeGoogle()
    for name in (
        "exchange_code",
        "userinfo",
        "refresh_access_token",
        "revoke",
        "list_events",
        "insert_event",
        "patch_event",
        "delete_event",
    ):
        monkeypatch.setattr(google, name, getattr(fake, name))
    return fake


def start_flow(client, **params):
    res = client.get(f"{API}/auth/google/start", params=params, follow_redirects=False)
    assert res.status_code == 302
    query = parse_qs(urlparse(res.headers["location"]).query)
    return query["state"][0], query


def finish_flow(client, state, code="code"):
    return client.get(
        f"{API}/auth/google/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )


def test_start_requests_offline_calendar_access(client):
    _, query = start_flow(client)
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert google.CALENDAR_SCOPE in query["scope"][0]
    assert query["redirect_uri"] == ["http://localhost:8000/api/v1/auth/google/callback"]


def test_google_login_creates_user_and_session(client, fake, db):
    state, _ = start_flow(client, next="/objectives")
    res = finish_flow(client, state)
    assert res.status_code == 302
    assert res.headers["location"] == "http://localhost:3000/objectives"

    me = client.get(f"{API}/users/me").json()
    assert me["email"] == "g@example.com" and me["full_name"] == "G"
    account = db.scalar(select(GoogleAccount))
    assert account.refresh_token and "refresh-1" not in account.refresh_token  # encrypted
    assert client.get(f"{API}/calendar/status").json() == {
        "connected": True,
        "email": "g@example.com",
    }


def test_callback_rejects_forged_state(client, fake):
    state, _ = start_flow(client)
    client.cookies.clear()  # a different browser than the one that started the flow
    res = finish_flow(client, state)
    assert res.headers["location"].endswith("/login?error=google_state")
    assert finish_flow(client, "garbage").headers["location"].endswith("error=google_state")
    assert client.get(f"{API}/users/me").status_code == 401


def test_next_cannot_leave_the_site(client, fake):
    state, _ = start_flow(client, next="//evil.com")
    assert finish_flow(client, state).headers["location"] == "http://localhost:3000/objectives"


def test_consent_denied(client, fake):
    state, _ = start_flow(client)
    res = client.get(
        f"{API}/auth/google/callback",
        params={"error": "access_denied", "state": state},
        follow_redirects=False,
    )
    assert res.headers["location"].endswith("/login?error=google_denied")


def test_google_login_takes_over_unverified_password_account(client, fake, db):
    fake.profile["email"] = CREDS["email"]
    client.post(f"{API}/auth/register", json=CREDS)  # squatter registers the address first
    client.post(f"{API}/auth/logout")

    state, _ = start_flow(client)
    finish_flow(client, state)  # the real owner signs in with Google

    user = db.scalar(select(User).where(User.email == CREDS["email"]))
    assert user.hashed_password is None
    assert client.post(f"{API}/auth/login", json=CREDS).status_code == 401


def test_connect_from_password_account(signed_in, fake, db):
    assert signed_in.get(f"{API}/calendar/status").json()["connected"] is False
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    assert signed_in.get(f"{API}/calendar/status").json()["connected"] is True
    assert db.scalar(select(User).where(User.email == CREDS["email"])).google_account


def test_google_account_cannot_be_shared(signed_in, client, fake):
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    signed_in.post(f"{API}/auth/logout")
    client.post(f"{API}/auth/register", json={"email": "b@example.com", "password": "supersecret"})
    state, _ = start_flow(client)
    res = finish_flow(client, state)
    assert res.headers["location"].endswith("/login?error=google")


def test_schedule_reschedule_unschedule(signed_in, fake):
    obj = signed_in.post(f"{API}/objectives", json=NEW).json()
    url = f"{API}/objectives/{obj['id']}/schedule"
    body = {"start": "2026-11-02T09:00:00+01:00"}

    assert signed_in.post(url, json=body).status_code == 409  # not connected yet
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)

    res = signed_in.post(url, json=body)
    assert res.status_code == 200
    scheduled = res.json()
    assert scheduled["event_id"] == "ev1"
    assert scheduled["event_start"].startswith("2026-11-02T08:00:00")  # stored as UTC
    assert scheduled["event_end"].startswith("2026-11-02T08:45:00")
    event = fake.events["ev1"]
    assert event["summary"] == "Deep work" and event["start"]["timeZone"] == "Africa/Lagos"

    moved = signed_in.post(url, json={"start": "2026-11-03T10:00:00Z", "minutes": 60}).json()
    assert moved["event_id"] == "ev1" and len(fake.events) == 1
    assert moved["event_end"].startswith("2026-11-03T11:00:00")

    fake.events.clear()  # deleted by hand in Google: rescheduling recreates it
    assert signed_in.post(url, json=body).json()["event_id"] == "ev1"

    cleared = signed_in.delete(url).json()
    assert cleared["event_id"] is None and cleared["event_start"] is None
    assert fake.events == {}


def test_schedule_requires_timezone_offset(signed_in, fake):
    obj = signed_in.post(f"{API}/objectives", json=NEW).json()
    res = signed_in.post(
        f"{API}/objectives/{obj['id']}/schedule", json={"start": "2026-11-02T09:00:00"}
    )
    assert res.status_code == 422


def test_deleting_objective_removes_its_event(signed_in, fake):
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    obj = signed_in.post(f"{API}/objectives", json=NEW).json()
    signed_in.post(f"{API}/objectives/{obj['id']}/schedule", json={"start": "2026-11-02T09:00:00Z"})
    assert fake.events
    assert signed_in.delete(f"{API}/objectives/{obj['id']}").status_code == 204
    assert fake.events == {}


def test_day_schedule(signed_in, fake):
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    items = signed_in.get(f"{API}/calendar/events", params={"date": "2026-11-02"}).json()
    assert [i["title"] for i in items] == ["Standup", "(No title)"]
    assert datetime.fromisoformat(items[0]["start"]) == datetime(2026, 11, 2, 8, 30, tzinfo=UTC)
    # all-day event spans the user's (Lagos, UTC+1) local day
    assert datetime.fromisoformat(items[1]["start"]) == datetime(2026, 11, 1, 23, 0, tzinfo=UTC)


def test_access_token_cached_then_refreshed(signed_in, fake, db):
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    for _ in range(2):
        signed_in.get(f"{API}/calendar/events", params={"date": "2026-11-02"})
    assert fake.refreshes == 0  # login token still valid

    account = db.scalar(select(GoogleAccount))
    account.access_token_expires_at = datetime(2020, 1, 1, tzinfo=UTC)
    db.commit()
    signed_in.get(f"{API}/calendar/events", params={"date": "2026-11-02"})
    assert fake.refreshes == 1


def test_disconnect(signed_in, fake):
    state, _ = start_flow(signed_in)
    finish_flow(signed_in, state)
    assert signed_in.post(f"{API}/calendar/disconnect").status_code == 204
    assert "revoke" in fake.calls
    assert signed_in.get(f"{API}/calendar/status").json()["connected"] is False
    assert signed_in.get(f"{API}/calendar/events", params={"date": "2026-11-02"}).status_code == 409
