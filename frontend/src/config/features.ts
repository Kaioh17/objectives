import { clientEnv } from "./env.client";

// Simple env-driven flags: NEXT_PUBLIC_FEATURES=beta-ui,new-nav (needs a rebuild to change).
// For per-user or runtime flags, move to a flag service and keep this as the default.
const enabled = new Set(clientEnv.NEXT_PUBLIC_FEATURES);

export const hasFeature = (name: string) => enabled.has(name);
