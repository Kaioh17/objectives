from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.timezone import utcnow
from app.main import app
from app.models import User
from tests.conftest import CREDS, bearer

API = "/api/v1"


def test_health(client):
    assert client.get("/health").json() == {"message": "ok"}


def test_register_returns_access_token_and_refresh_cookie(client):
    res = client.post(f"{API}/auth/register", json=CREDS)
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["timezone"] == "Africa/Lagos"
    assert "hashed_password" not in body["user"]
    assert body["token_type"] == "bearer" and body["expires_in"] == 30 * 60
    assert "refresh_token" not in body and "set-cookie" in res.headers

    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert f"max-age={30 * 86400}" in cookie and f"path={API}/auth" in cookie

    claims = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert claims["typ"] == "access"
    assert 29 * 60 < claims["exp"] - utcnow().timestamp() <= 30 * 60

    bearer(client, body["access_token"])
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
    assert client.post(f"{API}/auth/refresh").status_code == 401  # cookie is gone

    wrong = client.post(f"{API}/auth/login", json={**CREDS, "password": "nope-nope"})
    assert wrong.status_code == 401
    missing = client.post(f"{API}/auth/login", json={**CREDS, "email": "x@example.com"})
    assert missing.status_code == 401 and missing.json() == wrong.json()

    login = client.post(f"{API}/auth/login", json=CREDS)
    assert login.status_code == 200
    bearer(client, login.json()["access_token"])
    assert client.get(f"{API}/users/me").status_code == 200
    assert client.post(f"{API}/auth/logout").status_code == 204
    assert client.post(f"{API}/auth/refresh").status_code == 401


def test_endpoints_require_session(client):
    for path in ("/users/me", "/objectives", "/calendar/status"):
        assert client.get(API + path).status_code == 401


def test_refresh_slides_the_login_forward(signed_in):
    res = signed_in.post(f"{API}/auth/refresh")
    assert res.status_code == 200
    assert res.json()["user"]["email"] == CREDS["email"]
    assert f"max-age={30 * 86400}" in res.headers["set-cookie"].lower()
    bearer(signed_in, res.json()["access_token"])
    assert signed_in.get(f"{API}/users/me").status_code == 200


def forge(kind, user_id=1, version=0, **overrides):
    exp = utcnow() + timedelta(hours=1)
    claims = {"sub": str(user_id), "ver": version, "typ": kind, "exp": exp}
    return jwt.encode({**claims, **overrides}, settings.secret_key, algorithm="HS256")


def test_expired_and_forged_tokens_rejected(signed_in):
    expired = utcnow() - timedelta(seconds=1)
    bearer(signed_in, forge("access", exp=expired))
    assert signed_in.get(f"{API}/users/me").status_code == 401

    bearer(signed_in, jwt.encode({"sub": "1", "ver": 0, "typ": "access"}, "x" * 40, "HS256"))
    assert signed_in.get(f"{API}/users/me").status_code == 401

    signed_in.cookies.set("refresh_token", forge("refresh", exp=expired), path=f"{API}/auth")
    assert signed_in.post(f"{API}/auth/refresh").status_code == 401


def test_token_kinds_are_not_interchangeable(signed_in):
    bearer(signed_in, forge("refresh"))
    assert signed_in.get(f"{API}/users/me").status_code == 401

    signed_in.cookies.clear()
    signed_in.cookies.set("refresh_token", forge("access"), path=f"{API}/auth")
    assert signed_in.post(f"{API}/auth/refresh").status_code == 401


def test_refresh_cookie_is_only_sent_to_auth_routes(signed_in):
    signed_in.headers.pop("Authorization")
    assert signed_in.get(f"{API}/users/me").status_code == 401  # cookie alone is not enough


def test_logout_all_revokes_every_device(signed_in):
    other = TestClient(app, base_url="http://localhost:8000")
    res = other.post(f"{API}/auth/login", json=CREDS)
    bearer(other, res.json()["access_token"])
    assert other.get(f"{API}/users/me").status_code == 200

    assert signed_in.post(f"{API}/auth/logout-all").status_code == 204
    assert signed_in.get(f"{API}/users/me").status_code == 401
    assert other.get(f"{API}/users/me").status_code == 401  # access token revoked at once
    assert other.post(f"{API}/auth/refresh").status_code == 401


def test_password_change_revokes_other_devices(signed_in):
    other = TestClient(app, base_url="http://localhost:8000")
    res = other.post(f"{API}/auth/login", json=CREDS)
    bearer(other, res.json()["access_token"])

    body = {"password": "brand-new-pass", "current_password": "wrong-wrong"}
    assert signed_in.patch(f"{API}/users/me", json=body).status_code == 403
    body["current_password"] = CREDS["password"]
    assert signed_in.patch(f"{API}/users/me", json=body).status_code == 200

    # This device keeps its refresh cookie, so it recovers with one refresh; the other cannot
    assert signed_in.get(f"{API}/users/me").status_code == 401
    refreshed = signed_in.post(f"{API}/auth/refresh")
    assert refreshed.status_code == 200
    bearer(signed_in, refreshed.json()["access_token"])
    assert signed_in.get(f"{API}/users/me").status_code == 200
    assert other.get(f"{API}/users/me").status_code == 401
    assert other.post(f"{API}/auth/refresh").status_code == 401


def test_deactivated_user_is_locked_out(signed_in, db):
    db.scalar(select(User)).is_active = False
    db.commit()
    assert signed_in.get(f"{API}/users/me").status_code == 401
    assert signed_in.post(f"{API}/auth/refresh").status_code == 401


def test_delete_account_cascades(signed_in, db):
    signed_in.post(f"{API}/objectives", json={"title": "x", "minutes": 30, "mode": "daily"})
    assert signed_in.delete(f"{API}/users/me").status_code == 204
    assert db.scalar(select(User)) is None
    assert signed_in.get(f"{API}/objectives").status_code == 401
    assert signed_in.post(f"{API}/auth/refresh").status_code == 401
