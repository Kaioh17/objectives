from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.timezone import utcnow
from app.main import app
from app.models import UserSession
from tests.conftest import CREDS

API = "/api/v1"


def test_health(client):
    assert client.get("/health").json() == {"message": "ok"}


def test_register_sets_long_lived_cookie(client):
    res = client.post(f"{API}/auth/register", json=CREDS)
    assert res.status_code == 201
    assert res.json()["timezone"] == "Africa/Lagos"
    assert "hashed_password" not in res.json()
    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert f"max-age={90 * 86400}" in cookie
    assert client.get(f"{API}/users/me").json()["email"] == CREDS["email"]


def test_duplicate_email_and_bad_input(client):
    client.post(f"{API}/auth/register", json=CREDS)
    assert client.post(f"{API}/auth/register", json=CREDS).status_code == 409
    bad_tz = {**CREDS, "email": "b@example.com", "timezone": "Mars/Base"}
    assert client.post(f"{API}/auth/register", json=bad_tz).status_code == 422
    long_pw = {**CREDS, "email": "c@example.com", "password": "é" * 40}
    assert client.post(f"{API}/auth/register", json=long_pw).status_code == 422


def test_login_logout(client):
    client.post(f"{API}/auth/register", json=CREDS)
    client.post(f"{API}/auth/logout")
    assert client.get(f"{API}/users/me").status_code == 401

    wrong = client.post(f"{API}/auth/login", json={**CREDS, "password": "nope-nope"})
    assert wrong.status_code == 401
    missing = client.post(f"{API}/auth/login", json={**CREDS, "email": "x@example.com"})
    assert missing.status_code == 401 and missing.json() == wrong.json()

    assert client.post(f"{API}/auth/login", json=CREDS).status_code == 200
    assert client.get(f"{API}/users/me").status_code == 200
    assert client.post(f"{API}/auth/logout").status_code == 204
    assert client.get(f"{API}/users/me").status_code == 401


def test_endpoints_require_session(client):
    for path in ("/users/me", "/objectives", "/calendar/status"):
        assert client.get(API + path).status_code == 401


def test_session_slides_forward(signed_in, db):
    session = db.scalar(select(UserSession))
    session.last_seen_at = utcnow() - timedelta(days=2)
    session.expires_at = utcnow() + timedelta(days=1)
    db.commit()

    res = signed_in.get(f"{API}/users/me")
    assert res.status_code == 200
    assert "set-cookie" in res.headers
    db.refresh(session)
    assert session.expires_at > utcnow() + timedelta(days=89)


def test_expired_session_rejected(signed_in, db):
    session = db.scalar(select(UserSession))
    session.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert signed_in.get(f"{API}/users/me").status_code == 401


def test_password_change_revokes_other_devices(signed_in, client):
    other = TestClient(app, base_url="http://localhost:8000")
    other.post(f"{API}/auth/login", json=CREDS)
    assert other.get(f"{API}/users/me").status_code == 200

    body = {"password": "brand-new-pass", "current_password": "wrong-wrong"}
    assert signed_in.patch(f"{API}/users/me", json=body).status_code == 403
    body["current_password"] = CREDS["password"]
    assert signed_in.patch(f"{API}/users/me", json=body).status_code == 200

    assert signed_in.get(f"{API}/users/me").status_code == 200
    assert other.get(f"{API}/users/me").status_code == 401


def test_delete_account_cascades(signed_in, db):
    signed_in.post(f"{API}/objectives", json={"title": "x", "minutes": 30, "mode": "daily"})
    assert signed_in.delete(f"{API}/users/me").status_code == 204
    assert db.scalar(select(UserSession)) is None
    assert signed_in.get(f"{API}/objectives").status_code == 401
