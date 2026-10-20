"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, currentUser, refreshSession, SIGNED_OUT_EVENT } from "@/lib/api-client";
import { logout } from "./api";
import type { User } from "@/lib/auth-schema";

type Session = {
  status: "loading" | "error" | "ready";
  user: User | null;
  retry: () => void;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession needs a SessionProvider");
  return value;
}

// Restores the login on a page load from the refresh cookie (unless a login just happened). That call also slides the
// cookie forward, so anyone who keeps coming back stays signed in. Sends the browser to /login
// when there is no valid cookie, or when the session ends later (SIGNED_OUT_EVENT).
export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  // Just logged in or registered: the token and user are already in memory, no refresh needed
  const [user, setUser] = useState<User | null>(currentUser);
  const [status, setStatus] = useState<Session["status"]>(user ? "ready" : "loading");

  const restore = useCallback(() => {
    refreshSession()
      .then((result) => {
        setUser(result.user);
        setStatus("ready");
      })
      .catch((error) => {
        if (error instanceof ApiError && error.status === 401) router.replace("/login");
        else setStatus("error");
      });
  }, [router]);

  const retry = useCallback(() => {
    setStatus("loading");
    restore();
  }, [restore]);

  useEffect(() => {
    if (!user) restore();
    const onSignedOut = () => router.replace("/login");
    window.addEventListener(SIGNED_OUT_EVENT, onSignedOut);
    return () => window.removeEventListener(SIGNED_OUT_EVENT, onSignedOut);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount only: user is the initial value
  }, [restore, router]);

  return (
    <SessionContext value={{ status, user, retry, signOut: logout }}>{children}</SessionContext>
  );
}

// Page content only renders for a signed-in user, so nothing below it ever fires a 401
export function SessionGate({ children }: { children: ReactNode }) {
  const { status, retry } = useSession();
  if (status === "ready") return children;
  if (status === "loading") {
    return (
      <p className="panel-empty" role="status">
        Loading…
      </p>
    );
  }
  return (
    <div className="panel-empty" role="alert">
      <p>Could not reach the server.</p>
      <button type="button" onClick={retry}>
        Try Again
      </button>
    </div>
  );
}
