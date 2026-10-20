# Objectives API

FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Neon PostgreSQL, cookie sessions, Google sign-in and Google Calendar.

## Contents

[Setup](#setup) · [Run](#run) · [Database](#database) · [Auth](#auth) · [Routes](#routes) · [Time](#time) · [Tests](#tests) · [Structure](#structure) · [Production](#production)

## Setup

Requires Python 3.11+.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill it in
```

Google sign-in and Calendar need an OAuth client, see [GOOGLE_SETUP.md](GOOGLE_SETUP.md).
Without it everything except the Google routes works.

## Run

```bash
fastapi dev        # development, reload, http://localhost:8000/api/v1/docs
fastapi run        # production
```

## Database

Neon is wired with `neon.ts`, and `neon deploy` writes the connection strings into `.env`.

| Variable | Used by | Notes |
| --- | --- | --- |
| `DATABASE_URL` | The running app | Neon's pooled (PgBouncer) string. Blank falls back to local SQLite. |
| `DATABASE_URL_UNPOOLED` | Alembic | Neon's direct string. DDL does not go through the pooler. |

Schema changes go through Alembic, never `create_all`:

```bash
alembic upgrade head                              # apply
alembic revision --autogenerate -m "add thing"    # after editing a model
alembic check                                     # fails if models and database differ
```

Table rules:

- Every table has an integer primary key, `created_at` and `updated_at` (`timestamptz`, UTC).
- `updated_at` is bumped by the ORM and by a Postgres trigger, so console edits count too.
- Every foreign key is `ON DELETE CASCADE` and indexed. Deleting a user removes all their data.
- There is no role column. Everyone is a regular user, and the admin works in the Neon console.

## Auth

Login is a long-lived server-side session, not a token the browser has to manage.

- A random token goes in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` in production). Only its SHA-256 is stored in `sessions`.
- It lasts `SESSION_DAYS` (90) and slides forward on any day the user returns, so active users stay signed in.
- Sessions can be revoked: `POST /auth/logout`, `POST /auth/logout-all`, and changing the password signs out every other device.
- Google tokens are encrypted with Fernet (key derived from `SECRET_KEY`) before they reach the database.

The frontend must send `credentials: "include"` on API requests.

## Routes

All under `/api/v1`. Everything except `/auth/*` and `/health` needs the session cookie.

| Route | Purpose |
| --- | --- |
| `POST /auth/register`, `/auth/login` | JSON body, sets the cookie, returns the user |
| `POST /auth/logout`, `/auth/logout-all` | End this session, or all of them |
| `GET /auth/google/start?next=/objectives` | Navigate the browser here. Signed out: Google login. Signed in: connects Calendar. |
| `GET /users/me`, `PATCH /users/me`, `DELETE /users/me` | Profile, timezone, password, delete account |
| `GET/POST /objectives`, `GET/PATCH/DELETE /objectives/{id}` | Objectives. List filters: `?archived=`, `?mode=` |
| `POST /objectives/{id}/schedule` | Create or move the Google Calendar event: `{start, minutes?}` |
| `DELETE /objectives/{id}/schedule` | Remove the event |
| `GET /calendar/status` | `{connected, email}` |
| `GET /calendar/events?date=YYYY-MM-DD` | The user's events for that local day |
| `POST /calendar/disconnect` | Revoke Google access and unlink |

Errors are `{"detail": "..."}`.
A Google failure is 502, and a missing or expired Calendar connection is 409.

## Time

Everything is stored and returned in UTC (`2026-11-02T08:00:00Z`).
`users.timezone` holds an IANA name such as `Africa/Lagos`.
The backend uses it only where the calendar day matters: listing a day's events and labelling Google events.
Request datetimes must carry an offset, and naive ones are rejected.

## Tests

```bash
pytest
ruff check . && ruff format .
```

Tests use in-memory SQLite and a fake Google client, so they need no network or credentials.

## Structure

`router/` (HTTP) → `services/` (logic) → `models/` (SQLAlchemy). `schemas/` holds Pydantic contracts, `auth/` holds hashing, encryption and the session dependencies, `core/` holds config, database, logging, errors and time helpers, `migrations/` holds Alembic.

## Production

- Set `ENVIRONMENT=production` and a real `SECRET_KEY`.
- Run `alembic upgrade head` on deploy.
- Set `CORS` to the exact frontend origin, and keep API and frontend on the same site.
- Put the app in Google "In production" status, see [GOOGLE_SETUP.md](GOOGLE_SETUP.md).
