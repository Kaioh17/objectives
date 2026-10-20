"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ComponentProps, type FormEvent } from "react";
import { ApiError, refreshSession } from "@/lib/api-client";
import { googleStartUrl, login, register } from "./api";

const COPY = {
  login: {
    title: "Log In",
    lede: "Welcome back. Pick up where you left off.",
    submit: "Log In",
    switchText: "New here?",
    switchLabel: "Create an Account",
    switchHref: "/signup",
  },
  signup: {
    title: "Create Account",
    lede: "Set your first objective in under a minute.",
    submit: "Create Account",
    switchText: "Already have an account?",
    switchLabel: "Log In",
    switchHref: "/login",
  },
} as const;

// Error codes the backend puts in /login?error= when the Google round trip fails
const GOOGLE_ERRORS: Record<string, string> = {
  google_state: "Google sign-in expired or started in another browser. Try again.",
  google_denied: "Google sign-in was cancelled.",
  google: "Google sign-in failed. Try again, or use your email.",
  google_unavailable: "Google sign-in is not set up yet. Use your email instead.",
};

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  );
}

function PasswordInput(props: Omit<ComponentProps<"input">, "type">) {
  const [shown, setShown] = useState(false);
  return (
    <div className="password-wrap">
      <input {...props} type={shown ? "text" : "password"} />
      <button
        type="button"
        className="password-toggle"
        aria-label={shown ? "Hide password" : "Show password"}
        aria-pressed={shown}
        onClick={() => setShown((v) => !v)}
      >
        {shown ? "Hide" : "Show"}
      </button>
    </div>
  );
}

export function AuthForm({ mode, error }: { mode: keyof typeof COPY; error?: string }) {
  const router = useRouter();
  const copy = COPY[mode];
  const [mismatch, setMismatch] = useState(false);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<string | null>((error && GOOGLE_ERRORS[error]) || null);

  // Someone with a live refresh cookie never needs this form: send them straight in
  useEffect(() => {
    refreshSession()
      .then(() => router.replace("/objectives"))
      .catch(() => {});
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (mode === "signup" && form.get("password") !== form.get("confirm")) {
      setMismatch(true);
      document.getElementById("confirm")?.focus();
      return;
    }

    const email = String(form.get("email"));
    const password = String(form.get("password"));
    setPending(true);
    setFailure(null);
    try {
      if (mode === "signup") await register(String(form.get("name")), email, password);
      else await login(email, password);
      router.replace("/objectives");
    } catch (err) {
      setFailure(err instanceof ApiError ? err.message : "Could not reach the server. Try again.");
      setPending(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="auth-title">
      <div className="dialog-intro">
        <h1 id="auth-title" className="auth-title">
          {copy.title}
        </h1>
        <p className="meta">{copy.lede}</p>
      </div>

      <a className="btn-quiet btn-bar auth-google" href={googleStartUrl()}>
        <span className="auth-google-label">
          <GoogleIcon />
          Continue with Google
        </span>
      </a>

      <p className="auth-divider">or use your email</p>

      <form onSubmit={onSubmit}>
        {mode === "signup" && (
          <div className="field">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              name="name"
              className="input"
              type="text"
              autoComplete="name"
              placeholder="Your name"
              required
            />
          </div>
        )}
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            className="input"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <PasswordInput
            id="password"
            name="password"
            className="input"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            minLength={mode === "signup" ? 8 : undefined}
            placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
            required
          />
        </div>
        {mode === "signup" && (
          <div className="field">
            <label htmlFor="confirm">Confirm Password</label>
            <PasswordInput
              id="confirm"
              name="confirm"
              className="input"
              autoComplete="new-password"
              placeholder="Repeat your password"
              aria-invalid={mismatch}
              aria-describedby={mismatch ? "confirm-error" : undefined}
              onChange={() => setMismatch(false)}
              required
            />
            {mismatch && (
              <p id="confirm-error" className="error" role="alert">
                Passwords do not match. Retype both and try again.
              </p>
            )}
          </div>
        )}
        {failure && (
          <p className="error auth-error" role="alert">
            {failure}
          </p>
        )}
        <button type="submit" className="btn-bar" disabled={pending}>
          {pending ? "Please wait…" : copy.submit}
          <span aria-hidden="true">&rarr;</span>
        </button>
      </form>

      <p className="auth-switch">
        {copy.switchText} <Link href={copy.switchHref}>{copy.switchLabel}</Link>
      </p>
    </section>
  );
}
