# Authentication

This describes how login, reloads and token expiry work.
The browser calls the API directly, and the app and the API must be same-site.

## Tokens

| Token | Lifetime | Where it lives | Sent as |
| --- | --- | --- | --- |
| Access token (JWT) | 30 minutes | JavaScript memory only, never storage | `Authorization: Bearer` header on every API call |
| Refresh token (JWT) | 30 days | HttpOnly cookie set by the API | Cookie, sent by the browser to `/api/v1/auth/*` only |

Both tokens carry the user's `token_version`.
The API rejects either one if it no longer matches the user's current value.

## Hosts

- **Dev:** the app runs on `http://localhost:3000` and the API on `http://localhost:8000`.
  Ports do not matter for "same site", so the `SameSite=Lax` refresh cookie is sent on direct calls.
- **Production:** use hosts that share a registrable domain, for example `app.example.com` and `api.example.com`.
  The API's `CORS` setting must list the exact app origin.
- **Do not** use `app.localhost` for the app while the API is on `localhost`.
  They are different sites, so login works but the refresh cookie is dropped and every reload signs you out.

## 1. Login

1. You submit the form on `/login`, and the browser sends `POST /auth/login`.
1. The API checks the password and replies with both tokens in one response.
   - The access token is in the JSON body, together with the user.
   - The refresh token is set as an HttpOnly cookie with path `/api/v1/auth`.
1. The frontend calls `startSession`, which keeps the access token and the user in memory.
1. The app navigates to `/objectives` on the client side.
1. `SessionProvider` finds the user already in memory and renders the page.
   No refresh call is made.

Registration works the same way.

## 2. Using the app

- Every API call sends the access token as a Bearer header.
- The refresh cookie is not used for these calls.

## 3. When the access token expires

1. The next API call returns 401.
1. `apiFetch` calls `POST /auth/refresh` once, and the browser attaches the refresh cookie on its own.
1. The API returns a new access token and sets a new refresh cookie with a full 30 days, so the login slides forward.
1. The original request is retried with the new token, and the user notices nothing.
1. If the refresh also returns 401, the cookie is dead.
   The app clears memory and sends the user to `/login`.
1. If the refresh fails for another reason, such as a network error, the user stays signed in and only that request fails.

## 4. Reload or a new tab

1. Memory is wiped, so the access token and the user are gone.
1. `SessionProvider` finds no user and calls `POST /auth/refresh` once.
   This is why the call happens on a reload: the cookie is the only thing that survives.
1. With a valid cookie, the API returns a new access token, the user and a renewed cookie, and the page renders.
1. Without a valid cookie, the call returns 401 and the user goes to `/login`.
1. Every reload renews the cookie, so anyone who returns within 30 days never has to log in again.

## 5. Logged-out visit

1. `/objectives` calls refresh, gets a 401 and redirects to `/login`.
1. The login form calls refresh once more to check for an existing session and gets another 401.
   If that check succeeded, it would send the user straight to `/objectives`.
1. These two 401s in the API log are expected.

## 6. Logout

- **Logout:** `POST /auth/logout` clears the cookie.
  Memory is cleared and the user goes to `/login`.
  An access token that was already issued stays valid for the rest of its 30 minutes, because tokens are stateless.
- **Logout all:** `POST /auth/logout-all` bumps `token_version`, which invalidates every access and refresh token on every device.
  The cookie is cleared as well.

## 7. Google sign-in

1. "Continue with Google" is a browser navigation to `GET /auth/google/start`, not a fetch.
1. The API sends the user to Google with a signed `state` and a nonce cookie that ties the callback to this browser.
1. Google redirects to `GOOGLE_REDIRECT_URI`, which is on the API (`http://localhost:8000/api/v1/auth/google/callback` in dev).
1. The API sets the refresh cookie and redirects to `FRONTEND_URL`.
1. The app loads with no token in memory, so `SessionProvider` calls refresh once and the user is signed in.

See `backend/GOOGLE_SETUP.md` for the Google Cloud setup.

## Where the code is

- `backend/app/router/auth.py`: the endpoints.
- `backend/app/services/auth.py`: issuing tokens and the refresh cookie.
- `frontend/src/lib/api-client.ts`: in-memory token, `startSession`, `refreshSession`, and the refresh-and-retry on 401.
- `frontend/src/features/auth/session.tsx`: `SessionProvider`, which restores the login on a page load.
- `frontend/src/features/auth/auth-form.tsx`: the login and signup form.
