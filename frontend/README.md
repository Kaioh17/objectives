# Next.js Boilerplate

Next.js (App Router), React, TypeScript. Conventions first: structure, env files, secrets, prod switches, UI defaults. Start here.

## Contents

[Setup](#setup) · [Run](#run) · [Environment](#environment-files) · [Secrets](#secrets) · [Prod switches](#prod-switches) · [Structure](#structure) · [UI conventions](#ui-conventions) · [Backend](#backend-fastapi) · [Docker](#docker) · [Checklist](#production-checklist)

## Setup

Requires Node 20.9+ (`.nvmrc` pins 22).

```bash
npm install                     # commit the generated package-lock.json
cp .env.example .env.local      # secrets and personal overrides (never committed)
npm run dev                     # http://localhost:3000
```

## Run

| Command | Purpose |
| --- | --- |
| `npm run dev` | Development server (loads `.env.development`) |
| `npm run build && npm start` | Production build and server (loads `.env.production`) |
| `npm run lint` / `typecheck` / `test` | ESLint, `tsc`, Vitest |
| `npm run format` / `format:check` | Prettier |
| `npm run audit -- <url...>` | Lighthouse + axe gate against a running production server (below) |

## Audit (Lighthouse + axe)

Every route must pass: Lighthouse 80+ on every category (gate: Performance 90+, the rest 100), mobile and desktop, and zero axe violations. Audit a production build, never `next dev`.

```bash
npm run build
SESSION_SECRET="$(openssl rand -base64 32)" npm start -- -p 3123 &   # a spare port; the server needs its secrets or every score reads 0
CHROME_PATH=/path/to/chrome npm run audit -- http://localhost:3123/ http://localhost:3123/other
```

`CHROME_PATH` is optional when Chrome is installed. Exit code 1 means fail; the output lists each failing audit. CI runs this on `/`; add every new route to the `Audit` step in `.github/workflows/ci.yml`. Rules and fixes: [skills/lighthouse-axe-gate](../skills/lighthouse-axe-gate/SKILL.md).

## Environment files

Next.js loads these in order, first match wins: real environment variables, `.env.$NODE_ENV.local`, `.env.local`, `.env.$NODE_ENV`, `.env`.

| File | Committed | Holds |
| --- | --- | --- |
| `.env.example` | Yes | Every variable, documented; no secret values |
| `.env.development` | Yes | Non-secret defaults for `next dev` |
| `.env.production` | Yes | Non-secret defaults for `next build`; replace the placeholder URL |
| `.env.local`, `.env*.local` | **No** | Real secrets and personal overrides |

Two kinds of variable, and the difference matters:

| | `NEXT_PUBLIC_*` | No prefix |
| --- | --- | --- |
| Visible to | Everyone (inlined into the browser bundle) | Server only |
| Resolved | **Build time**; changing one needs a rebuild | **Runtime** |
| Belongs here | API URL, app name, feature flags | Secrets, internal URLs |
| Read via | `clientEnv` (`src/config/env.client.ts`) | `serverEnv` (`src/config/env.server.ts`) |

All variables are validated with Zod. A bad or missing required value fails the build or server start with a readable message. `KEY=` (empty) counts as unset. `process.env` may only be read inside `src/config/` (ESLint enforces this).

`NODE_ENV` is set by Next.js (`development` / `production` / `test`) and cannot express staging. Use `NEXT_PUBLIC_APP_ENV` (`development` | `staging` | `production`) for your own environment:

```bash
NEXT_PUBLIC_APP_ENV=staging npm run build
```

### Domains

The landing page (`/`) is served from `NEXT_PUBLIC_SITE_URL`; everything else (`/login`, `/signup`, `/objectives`) from `NEXT_PUBLIC_APP_URL`. `src/proxy.ts` redirects between them by host. In dev both are `http://localhost:3000`, so the proxy does nothing.

Production domains (`NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_API_URL`) are never committed. Set them in `.env.production.local` (git-ignored) or the platform env / Docker build args; the build fails if they are missing.

## Secrets

1. **Never commit them.** `.env*.local` is git-ignored. Only `.env.example` (empty values) documents them.
2. **`NEXT_PUBLIC_` is public.** Anything with that prefix ships to every browser. No keys, tokens, or passwords.
3. **Server secrets have no prefix** and are read only through `serverEnv`. The `server-only` import makes the build fail if a client component ever imports it.
4. **Inject in production from a secret store** (your platform's env settings, Kubernetes Secrets, AWS Secrets Manager / SSM, Docker `-e` / `--env-file`), not from files in the repo or image. The `Dockerfile` and CI build need no secrets.
5. **Keep tokens out of JavaScript-readable storage.** Prefer httpOnly, Secure, SameSite cookies set by the server over `localStorage`.
6. **Scan and rotate.** Run a secret scanner (for example gitleaks) in pre-commit and CI. If a secret leaks, rotate it; deleting the commit is not enough.

Add new secrets in three places: `.env.example` (documented, empty), `serverSchema` in `src/config/env.schema.ts`, and your secret store.

## Prod switches

Branch on `siteConfig` / `hasFeature`, never on raw env:

| Switch | Where | Effect |
| --- | --- | --- |
| `NEXT_PUBLIC_APP_ENV` | `src/config/site.ts` (`isProduction`) | `robots.txt` blocks crawlers outside production; the home page shows the environment outside production |
| `NEXT_PUBLIC_FEATURES` | `src/config/features.ts` (`hasFeature("x")`) | Comma-separated flags, rebuild to change |
| `BUILD_STANDALONE=true` | `next.config.ts` | Standalone server output for Docker |
| Security headers | `next.config.ts` | Baseline headers everywhere; HSTS only in production |

Add a Content-Security-Policy once you know your third-party origins.

## Structure

```
src/
├── app/            routing only: layouts, pages, route handlers (thin)
├── features/       one folder per domain; expose a public API via index.ts
├── components/ui/  generic, feature-agnostic components
├── hooks/          shared hooks
├── lib/            framework-agnostic helpers (api-client.ts)
├── config/         env, site config, feature flags
├── styles/         global CSS and tokens
├── types/          shared types
└── instrumentation.ts   exits on invalid server env at boot
```

Import direction is `app` → `features` → `components/ui` → `lib` / `config`, never the reverse. Features do not reach into each other's internals. Import with the `@/` alias (`@/config/site`).

**Add a feature `foo`:** create `src/features/foo/{components,hooks,api,types}/` and an `index.ts`, then use it from a page in `src/app/`.

## UI conventions

Defaults follow [web-design-guidelines](../skills/web-design-guidelines/SKILL.md) and are already in `src/styles/globals.css` and `src/app/layout.tsx`:

- Skip link and one `<main>` landmark; `<html lang>` set; zoom never disabled.
- Visible `:focus-visible` outline; never `outline: none` without a replacement.
- `prefers-reduced-motion` honored; animate `transform` / `opacity` only; never `transition: all`.
- Light and dark themes via `color-scheme` and tokens; `theme-color` matches the page.
- `<button>` for actions, `<a>` / `<Link>` for navigation; every input has a label; icon-only buttons have `aria-label`.
- Images get explicit `width` and `height`; `next/image` for content images. Ship an icon (`src/app/icon.svg`): a missing favicon logs a console 404 and costs Best Practices points.
- Every route exports `metadata` with a title and description (SEO).
- Copy: Title Case buttons and headings, specific labels ("Save API Key"), error messages say what to do next, loading text ends with `…`.

## Backend (FastAPI)

The app talks to the Objectives API in `../backend`.

- **Direct calls.** The browser calls the API at `NEXT_PUBLIC_API_URL` (`http://localhost:8000/api/v1` in dev), so the backend `CORS` must list the app origin.
  The backend's refresh cookie is `SameSite=Lax`, and `app.localhost` and `localhost` are different sites, so the app and API must be same-site: `localhost:3000` and `localhost:8000` in dev, `app.example.com` and `api.example.com` in production.
- **Auth.** Login returns a 30 minute access JWT that lives in memory (`src/lib/api-client.ts`) and goes out as a Bearer header. The 30 day refresh token is an HttpOnly cookie the browser holds, never JavaScript.
  `SessionProvider` (`src/features/auth/session.tsx`) calls `POST /auth/refresh` on every page load, which restores the login and slides the cookie another 30 days.
  `apiFetch` also refreshes once and retries on any 401. If the cookie is rejected the app is signed out and sent to `/login`.
- **Data.** Objectives and calendar calls go through `apiFetch` (`src/features/objectives/store.ts`, `src/features/calendar/api.ts`). Errors are `ApiError` with the backend's `detail` message.
- **Google.** "Continue with Google" and "Connect Google Calendar" are plain navigations to `/auth/google/start`. Google rejects `*.localhost` redirect URIs, see `../backend/GOOGLE_SETUP.md` for the local setup.
- Health: this app serves `/api/health`; the backend serves `/health`.

## Docker

```bash
docker build -t web .
docker run -p 3000:3000 -e SESSION_SECRET="$(openssl rand -base64 32)" web
```

Override build-time values with `--build-arg NEXT_PUBLIC_APP_ENV=staging --build-arg NEXT_PUBLIC_API_URL=...`. Runtime secrets go in with `-e` or your orchestrator's secret mechanism.

## Production checklist

- [ ] `.env.production` has the real API URL; `NEXT_PUBLIC_APP_ENV` is correct per environment
- [ ] `SESSION_SECRET` (and any other secret) comes from the secret store
- [ ] HTTPS in front; HSTS is on automatically in production
- [ ] CSP added; `X-Frame-Options` reviewed if the app is embedded
- [ ] `NEXT_PUBLIC_API_URL` is a same-site API host + `/api/v1`, and backend `CORS` lists the app origin
- [ ] Error reporting wired into `src/app/error.tsx`
- [ ] CI green (`format:check`, lint, typecheck, test, build, audit) and dependencies audited
- [ ] `npm run audit` passes on every route (Lighthouse 80+ floor, 90+ gate, axe 0)
