import "server-only"; // importing this from a client component fails the build
import { clientEnv } from "./env.client";
import { parseServerEnv } from "./env.schema";

// Secrets live here. Use the build-time app env (not runtime process.env) for the
// environment, because NEXT_PUBLIC_* are not present in a standalone container's env.
export const serverEnv = parseServerEnv(process.env, clientEnv.NEXT_PUBLIC_APP_ENV);
