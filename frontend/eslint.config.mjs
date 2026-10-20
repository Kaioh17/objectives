import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // Keep env access in one place so it stays validated
    rules: {
      "no-restricted-properties": [
        "error",
        {
          object: "process",
          property: "env",
          message: "Read env through src/config (env.client.ts / env.server.ts).",
        },
      ],
    },
  },
  {
    files: [
      "src/config/**",
      "src/instrumentation*.ts",
      "next.config.ts",
      "vitest.config.mts",
      "**/*.test.ts",
    ],
    rules: { "no-restricted-properties": "off" },
  },
  globalIgnores([".next/**", "out/**", "build/**", "coverage/**", "next-env.d.ts"]),
]);
