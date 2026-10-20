"use client";

import { useEffect } from "react";

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    // Send to your error reporter here (Sentry, etc.)
    console.error(error);
  }, [error]);

  return (
    <div role="alert">
      <h1>Something Went Wrong</h1>
      <p>An unexpected error occurred. Try again, or reload the page if it keeps happening.</p>
      <button type="button" onClick={reset}>
        Try Again
      </button>
    </div>
  );
}
