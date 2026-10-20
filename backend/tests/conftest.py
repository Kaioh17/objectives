import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.models import Base

# HS256 wants 32+ bytes; keeps tests independent of .env
settings.secret_key = "test-secret-key-that-is-at-least-32-bytes"
settings.google_client_id = "test-client-id"
settings.google_client_secret = "test-client-secret"
settings.environment = "development"
# Pinned so a developer's own .env cannot change what the tests expect
settings.frontend_url = "http://localhost:3000"
settings.google_redirect_uri = "http://localhost:8000/api/v1/auth/google/callback"

# In-memory DB shared across threads
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
enable_sqlite_foreign_keys(engine)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    with TestSession() as db:
        yield db


@pytest.fixture
def client():
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_get_db
    # No context manager: skips lifespan so the real DB is untouched
    yield TestClient(app, base_url="http://localhost:8000")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    with TestSession() as session:
        yield session


CREDS = {"email": "a@example.com", "password": "supersecret", "timezone": "Africa/Lagos"}


def bearer(client, token):
    client.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture
def signed_in(client):
    """A client holding the refresh cookie and an access token for CREDS."""
    res = client.post("/api/v1/auth/register", json=CREDS)
    assert res.status_code == 201
    bearer(client, res.json()["access_token"])
    return client
