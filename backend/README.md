# Objectives API

FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Neon PostgreSQL, JWT auth, Google sign-in and Google Calendar.

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

Login is two stateless JWTs signed with `SECRET_KEY`. Nothing about a login is stored in the database.

- The access token lives `ACCESS_TOKEN_MINUTES` (30). `login`, `register` and `refresh` return it in the JSON body.
  The client keeps it in memory and sends `Authorization: Bearer <token>`.
- The refresh token lives `REFRESH_TOKEN_DAYS` (30) in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` in production), scoped to `/api/v1/auth` so it only travels to auth routes.
- `POST /auth/refresh` trades the cookie for a new access token and sets a new 30 day cookie.
  Every refresh restarts the 30 days, so a user who keeps coming back is never signed out.
- On page load, or after any 401, the client calls `/auth/refresh` once and retries. A 401 from `/auth/refresh` itself means the user must log in.
- `users.token_version` is inside every token. Bumping it kills all of them at once, which is what `POST /auth/logout-all`, a password change and a Google takeover of an unverified account do.
  `POST /auth/logout` only clears the cookie on this device, so an access token already issued works until it expires.
- Changing the password keeps this device signed in by re-issuing its cookie, but its old access token is revoked, so the client must call `/auth/refresh` right after.
- Google tokens are encrypted with Fernet (key derived from `SECRET_KEY`) before they reach the database.

The frontend must send `credentials: "include"` on API requests.

## Routes

All under `/api/v1`. Everything except `/auth/*` and `/health` needs a Bearer access token.

| Route | Purpose |
| --- | --- |
| `POST /auth/register`, `/auth/login` | JSON body, sets the refresh cookie, returns `{access_token, expires_in, user}` |
| `POST /auth/refresh` | Refresh cookie in, new access token and a new 30 day cookie out |
| `POST /auth/logout`, `/auth/logout-all` | Clear this device's cookie, or revoke every device |
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

`router/` (HTTP) → `services/` (logic) → `models/` (SQLAlchemy). `schemas/` holds Pydantic contracts, `auth/` holds hashing, encryption, JWTs and the auth dependencies, `core/` holds config, database, logging, errors and time helpers, `migrations/` holds Alembic.

## Production

- Set `ENVIRONMENT=production` and a real `SECRET_KEY`.
- Run `alembic upgrade head` on deploy.
- The browser calls the API directly: set `CORS` to the exact frontend origin and keep API and frontend on the same site (for example `app.example.com` and `api.example.com`), because the refresh cookie is `SameSite=Lax`.
- Put the app in Google "In production" status, see [GOOGLE_SETUP.md](GOOGLE_SETUP.md).
