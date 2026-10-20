import { z } from "zod";

// Pure schemas + parsers (no server-only, no process.env) so they are unit-testable.

export const appEnvSchema = z.enum(["development", "staging", "production"]);
export type AppEnv = z.infer<typeof appEnvSchema>;

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, "");

// NEXT_PUBLIC_*: build-time, public. Required values have no default so a
// misconfigured prod build fails loudly instead of silently running as "development".
export const clientSchema = z.object({
  NEXT_PUBLIC_APP_ENV: appEnvSchema,
  NEXT_PUBLIC_APP_NAME: z.string().min(1).default("Next Boilerplate"),
  NEXT_PUBLIC_API_URL: z.url().transform(trimTrailingSlash),
  // Origins of the landing page and of the app (login, signup, objectives). No trailing slash.
  // Real domains live only in env files / the platform's env, never in source.
  NEXT_PUBLIC_SITE_URL: z.url().transform(trimTrailingSlash),
  NEXT_PUBLIC_APP_URL: z.url().transform(trimTrailingSlash),
  NEXT_PUBLIC_FEATURES: z
    .string()
    .default("")
    .transform((value) =>
      value
        .split(",")
        .map((flag) => flag.trim())
        .filter(Boolean),
    ),
});

// Server-only: runtime, secret. Never exposed to the browser.
export const serverSchema = z.object({
  API_INTERNAL_URL: z.url().transform(trimTrailingSlash).optional(),
  SESSION_SECRET: z.string().min(32).optional(),
});

type Source = Record<string, string | undefined>;

// `KEY=` (empty) counts as unset, so defaults and required checks behave the same
function omitEmpty(source: Source): Source {
  return Object.fromEntries(Object.entries(source).filter(([, value]) => value));
}

function parseEnv<S extends z.ZodType>(schema: S, source: Source): z.output<S> {
  const result = schema.safeParse(omitEmpty(source));
  if (!result.success) {
    throw new Error(`Invalid environment variables:\n${z.prettifyError(result.error)}`);
  }
  return result.data;
}

export const parseClientEnv = (source: Source) => parseEnv(clientSchema, source);

export function parseServerEnv(source: Source, appEnv: AppEnv) {
  const schema = serverSchema.refine(
    (env) => appEnv === "development" || env.SESSION_SECRET !== undefined,
    { path: ["SESSION_SECRET"], message: `Required when NEXT_PUBLIC_APP_ENV is "${appEnv}"` },
  );
  return parseEnv(schema, source);
}
