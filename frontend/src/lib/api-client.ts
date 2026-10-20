import { siteConfig } from "@/config/site";
import { authResultSchema, type AuthResult, type User } from "@/lib/auth-schema";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// The short-lived access JWT lives in memory only. The long-lived refresh token is an HttpOnly
// cookie the browser sends on its own, so a page reload restores the session via /auth/refresh.
let accessToken: string | null = null;
let sessionUser: User | null = null;
let refreshing: Promise<AuthResult> | null = null;

export const SIGNED_OUT_EVENT = "auth:signed-out";

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

// Login and register return the token and the user together, so the app can start from them
// without a /auth/refresh round trip
export function startSession(result: AuthResult) {
  accessToken = result.access_token;
  sessionUser = result.user;
}

export const currentUser = () => (accessToken ? sessionUser : null);

// The login is over (logout, or the refresh cookie was rejected): forget the token and tell the app
export function endSession() {
  accessToken = null;
  sessionUser = null;
  if (typeof window !== "undefined") window.dispatchEvent(new Event(SIGNED_OUT_EVENT));
}

type Options = Omit<RequestInit, "body"> & {
  json?: unknown;
  // false for the auth endpoints themselves: no Bearer header, no refresh-and-retry on 401
  auth?: boolean;
};

async function send(path: string, { json, auth = true, ...init }: Options): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (json !== undefined) headers.set("Content-Type", "application/json");
  if (auth && accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(`${siteConfig.apiUrl}${path}`, {
    ...init,
    headers,
    credentials: "include",
    body: json === undefined ? undefined : JSON.stringify(json),
  });
}

// Errors follow FastAPI's shape: { detail: string }. Request validation sends a list instead.
async function toError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  const detail =
    typeof body?.detail === "string"
      ? body.detail
      : response.status === 422
        ? "Some of the details are not valid."
        : response.statusText;
  return new ApiError(response.status, detail || "Something went wrong.");
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) throw await toError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// Trades the refresh cookie for a new access token (and the backend slides the cookie another
// 30 days). Concurrent callers share one request: the backend would accept both, but each
// would needlessly rotate the cookie.
export function refreshSession(): Promise<AuthResult> {
  refreshing ??= send("/auth/refresh", { method: "POST", auth: false })
    .then((response) => parse<unknown>(response))
    .then((body) => {
      const result = authResultSchema.parse(body);
      startSession(result);
      return result;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

// Typed wrapper over fetch. A 401 triggers one silent refresh and a retry; if that fails too
// the user is signed out and the app is told through SIGNED_OUT_EVENT.
export async function apiFetch<T>(path: string, options: Options = {}): Promise<T> {
  let response = await send(path, options);
  if (response.status === 401 && options.auth !== false) {
    try {
      await refreshSession();
      response = await send(path, options);
    } catch (error) {
      // Only a rejected refresh cookie ends the session; a network blip must not log anyone out
      if (error instanceof ApiError && error.status === 401) {
        endSession();
      } else {
        throw error;
      }
    }
  }
  return parse<T>(response);
}
