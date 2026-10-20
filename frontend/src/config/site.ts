import { clientEnv } from "./env.client";

// Environment switches live here; branch on these instead of reading env ad hoc
export const siteConfig = {
  name: clientEnv.NEXT_PUBLIC_APP_NAME,
  description: "Set daily, weekly and monthly objectives and schedule them on your calendar.",
  env: clientEnv.NEXT_PUBLIC_APP_ENV,
  isProduction: clientEnv.NEXT_PUBLIC_APP_ENV === "production",
  apiUrl: clientEnv.NEXT_PUBLIC_API_URL,
  siteUrl: clientEnv.NEXT_PUBLIC_SITE_URL,
  appUrl: clientEnv.NEXT_PUBLIC_APP_URL,
} as const;
