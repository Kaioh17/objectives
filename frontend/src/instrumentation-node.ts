// Invalid server env exits the process so orchestrators see a failed start, instead of a
// server that stays up and answers 500. Skipped during `next build` (secrets are runtime-only).
if (process.env.NEXT_PHASE !== "phase-production-build") {
  try {
    await import("@/config/env.server");
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
}

export {};
