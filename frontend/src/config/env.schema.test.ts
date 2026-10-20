import { describe, expect, it } from "vitest";
import { parseClientEnv, parseServerEnv } from "./env.schema";

const base = {
  NEXT_PUBLIC_APP_ENV: "development",
  NEXT_PUBLIC_API_URL: "http://localhost:8000/api/v1/",
  NEXT_PUBLIC_SITE_URL: "http://localhost:3000/",
  NEXT_PUBLIC_APP_URL: "http://app.localhost:3000",
};

describe("parseClientEnv", () => {
  it("applies defaults and normalizes values", () => {
    const env = parseClientEnv({ ...base, NEXT_PUBLIC_FEATURES: " beta-ui, ,new-nav " });
    expect(env.NEXT_PUBLIC_APP_NAME).toBe("Next Boilerplate");
    expect(env.NEXT_PUBLIC_API_URL).toBe("http://localhost:8000/api/v1");
    expect(env.NEXT_PUBLIC_FEATURES).toEqual(["beta-ui", "new-nav"]);
    expect(env.NEXT_PUBLIC_SITE_URL).toBe("http://localhost:3000");
    expect(env.NEXT_PUBLIC_APP_URL).toBe("http://app.localhost:3000");
  });

  it("requires both origins", () => {
    expect(() => parseClientEnv({ ...base, NEXT_PUBLIC_APP_URL: "" })).toThrow(
      /NEXT_PUBLIC_APP_URL/,
    );
    expect(() => parseClientEnv({ ...base, NEXT_PUBLIC_SITE_URL: "" })).toThrow(
      /NEXT_PUBLIC_SITE_URL/,
    );
  });

  it("treats empty strings as unset", () => {
    expect(() => parseClientEnv({ ...base, NEXT_PUBLIC_API_URL: "" })).toThrow(
      /NEXT_PUBLIC_API_URL/,
    );
  });

  it("rejects an unknown app env", () => {
    expect(() => parseClientEnv({ ...base, NEXT_PUBLIC_APP_ENV: "prod" })).toThrow(
      /NEXT_PUBLIC_APP_ENV/,
    );
  });
});

describe("parseServerEnv", () => {
  const secret = "x".repeat(32);

  it("does not require a secret in development", () => {
    expect(parseServerEnv({}, "development").SESSION_SECRET).toBeUndefined();
  });

  it("requires SESSION_SECRET outside development", () => {
    expect(() => parseServerEnv({}, "production")).toThrow(/SESSION_SECRET/);
    expect(parseServerEnv({ SESSION_SECRET: secret }, "staging").SESSION_SECRET).toBe(secret);
  });

  it("rejects a short secret", () => {
    expect(() => parseServerEnv({ SESSION_SECRET: "short" }, "development")).toThrow(
      /SESSION_SECRET/,
    );
  });
});
