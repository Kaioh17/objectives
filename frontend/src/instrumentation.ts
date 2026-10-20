// Runs once at server start. Node-only work lives in a separate file so the Edge build stays clean.
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./instrumentation-node");
  }
}
