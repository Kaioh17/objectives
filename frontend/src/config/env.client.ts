import { parseClientEnv } from "./env.schema";

// Each NEXT_PUBLIC_* must be referenced statically: Next.js inlines them at build time
// and cannot see dynamic access such as process.env[name] or a spread of process.env.
export const clientEnv = parseClientEnv({
  NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL,
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  NEXT_PUBLIC_FEATURES: process.env.NEXT_PUBLIC_FEATURES,
});
