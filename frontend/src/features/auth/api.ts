import { siteConfig } from "@/config/site";
import { apiFetch, endSession, startSession } from "@/lib/api-client";
import { authResultSchema, type User } from "@/lib/auth-schema";

async function start(path: string, json: unknown): Promise<User> {
  const result = authResultSchema.parse(
    await apiFetch(path, { method: "POST", json, auth: false }),
  );
  startSession(result);
  return result.user;
}

export const login = (email: string, password: string) => start("/auth/login", { email, password });

// The browser's zone is the best guess for the account's IANA timezone, which the backend uses
// to decide where a calendar day starts
export const register = (name: string, email: string, password: string) =>
  start("/auth/register", {
    email,
    password,
    full_name: name,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

// Idempotent. Clears the refresh cookie, so it must succeed before the session counts as ended
export async function logout(): Promise<void> {
  await apiFetch("/auth/logout", { method: "POST", auth: false });
  endSession();
}

// Google is a browser navigation, not a fetch: it bounces through Google and back to /objectives
export const googleStartUrl = (next = "/objectives") =>
  `${siteConfig.apiUrl}/auth/google/start?next=${encodeURIComponent(next)}`;
