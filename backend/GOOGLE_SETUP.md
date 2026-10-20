# Google Cloud setup

One OAuth client powers both "Continue with Google" (login) and Google Calendar (scheduling objectives).
The backend asks for everything in a single consent screen, so users approve once.
Do these steps once per environment (local, production).

## 1. Create a project

1. Open <https://console.cloud.google.com/>.
1. Click the project picker at the top, then **New project**.
1. Name it `objectives` and click **Create**, then switch to it.

## 2. Enable the Calendar API

1. Go to **APIs & Services > Library**.
1. Search for **Google Calendar API** and click **Enable**.

Sign-in itself needs no extra API.

## 3. Configure the consent screen

Google now calls this area **Google Auth Platform**.
Open it from the left menu, or search for "Google Auth Platform" in the top bar.

1. Click **Get started**.
1. App name: `Objectives` (users see this on the consent screen). User support email: your email.
1. Audience: **External**.
1. Contact information: your email. Accept the policy and click **Create**.

## 4. Add the scopes

Under **Data Access**, click **Add or remove scopes** and tick these four, then **Update** and **Save**:

| Scope | Why |
| --- | --- |
| `openid` | Identify the Google account |
| `.../auth/userinfo.email` | Account email, used to match or create the user |
| `.../auth/userinfo.profile` | Name |
| `.../auth/calendar.events` | Read and create events on the user's calendar |

`calendar.events` is a **sensitive** scope.
That has consequences, see step 8.

## 5. Add yourself as a test user

While the app is in **Testing**, only listed accounts can sign in.

1. Open **Audience**.
1. Under **Test users**, click **Add users** and add your own Google address (and anyone else trying it).

## 6. Create the OAuth client

1. Open **Clients** and click **Create client**.
1. Application type: **Web application**. Name: `objectives-backend`.
1. **Authorized JavaScript origins**: leave empty. The browser never talks to Google directly, the backend does.
1. **Authorized redirect URIs**: add exactly
   - `http://localhost:8000/api/v1/auth/google/callback` for local development
   - `https://api.yourdomain.com/api/v1/auth/google/callback` for production, once you have the domain
1. Click **Create** and copy the **Client ID** and **Client secret**.

The redirect URI must match `GOOGLE_REDIRECT_URI` character for character, including scheme, port and path.

## 7. Fill in `backend/.env`

```dotenv
GOOGLE_CLIENT_ID=<client id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<client secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

The browser calls the API directly, so the callback lands on the API and sets the refresh cookie there.
The cookie is `SameSite=Lax`, so the app (`localhost:3000`) and the API (`localhost:8000`) must be same-site.
Google rejects `*.localhost` hosts such as `app.localhost`, so keep both on plain `localhost` in development.
The frontend defaults in `frontend/.env.development` already do this.

Restart the server, then try it:

1. Start the API with `fastapi dev` and the frontend with `npm run dev`.
1. Open <http://localhost:3000/login> and click **Continue with Google**.
1. Pick your account.
   Google shows "Google hasn't verified this app" while the app is unverified.
   Click **Advanced** and then **Go to Objectives (unsafe)**. This is expected for your own project.
1. Leave the **calendar** checkbox ticked.
   Google lets users untick individual permissions, and the backend then reports `connected: false` from `GET /api/v1/calendar/status`.
1. You land on `FRONTEND_URL/objectives` with the refresh cookie set.
   The frontend then calls `POST /api/v1/auth/refresh` to get its first access token.

## 8. Before real users arrive

**Refresh tokens expire after 7 days in Testing.**
Users then see "Google Calendar access expired, connect Google again".
To stop that, open **Audience** and click **Publish app** to move it to **In production**.

**Unverified apps are capped at 100 users and show the warning screen.**
Removing the warning means passing Google's verification, because `calendar.events` is sensitive.
You will need:

- A homepage and a privacy policy on a domain you own (verified in Google Search Console).
- Both links added under **Branding**.
- A short screen recording of the consent flow showing how Calendar data is used.
- A scope justification: "creates and lists events so users can schedule their objectives".

Verification takes days to weeks, so start it early.
You can ship to a handful of test users in the meantime.

## 9. Production settings

- Serve the API from a host that is **same-site** with the app, for example `app.example.com` and `api.example.com`, with the redirect URI on the API host.
  The refresh cookie is `SameSite=Lax`, so it will not be sent between unrelated domains.
- Set `ENVIRONMENT=production` (marks the cookie `Secure`), a real `SECRET_KEY`, `FRONTEND_URL`, and `CORS` with the exact frontend origin.
- Add the production redirect URI to the OAuth client (step 6).
- The frontend must send `credentials: "include"` on every API request, or the refresh cookie is dropped.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `redirect_uri_mismatch` | The URI in the client differs from `GOOGLE_REDIRECT_URI`. Compare character by character. |
| `access_denied` on the consent screen | Your account is not in **Test users** (step 5). |
| Returns to `/login?error=google_denied` | You pressed Cancel on the consent screen. |
| Returns to `/login?error=google_state` | The flow started in a different browser, or took more than 10 minutes. Try again. |
| `connected: false` after signing in | The calendar permission was unticked. Visit `/auth/google/start` again. |
| `invalid_grant` or "connect Google again" | The refresh token was revoked or expired. Remove the app at <https://myaccount.google.com/permissions> and reconnect. |
