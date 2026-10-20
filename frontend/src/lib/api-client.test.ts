import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/config/site", () => ({ siteConfig: { apiUrl: "http://api.test/api/v1" } }));

const user = { id: 1, email: "a@example.com", full_name: null, timezone: "UTC" };
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

// Each test gets a fresh module, so the in-memory access token starts empty
async function load() {
  vi.resetModules();
  return import("./api-client");
}

describe("apiFetch", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => vi.stubGlobal("fetch", fetchMock));
  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  const bearer = (call: number) =>
    new Headers(fetchMock.mock.calls[call]![1]?.headers).get("Authorization");

  it("sends the access token and the cookie", async () => {
    const { apiFetch, setAccessToken } = await load();
    setAccessToken("tok-1");
    fetchMock.mockResolvedValueOnce(json([]));
    await apiFetch("/objectives");
    expect(bearer(0)).toBe("Bearer tok-1");
    expect(fetchMock.mock.calls[0]![1]?.credentials).toBe("include");
  });

  it("refreshes once on 401 and retries with the new token", async () => {
    const { apiFetch, setAccessToken } = await load();
    setAccessToken("stale");
    fetchMock
      .mockResolvedValueOnce(json({ detail: "Not signed in" }, 401))
      .mockResolvedValueOnce(json({ access_token: "fresh", user }))
      .mockResolvedValueOnce(json({ ok: true }));
    await expect(apiFetch("/objectives", { method: "POST", json: { a: 1 } })).resolves.toEqual({
      ok: true,
    });
    expect(fetchMock.mock.calls[1]![0]).toBe("http://api.test/api/v1/auth/refresh");
    expect(bearer(2)).toBe("Bearer fresh");
    expect(fetchMock.mock.calls[2]![1]?.body).toBe('{"a":1}'); // body is re-sent on the retry
  });

  it("shares one refresh between concurrent 401s", async () => {
    const { apiFetch } = await load();
    fetchMock.mockImplementation(async (url) =>
      String(url).endsWith("/auth/refresh")
        ? json({ access_token: "fresh", user })
        : new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).get("Authorization")
          ? json({ ok: true })
          : json({ detail: "Not signed in" }, 401),
    );
    await Promise.all([apiFetch("/a"), apiFetch("/b")]);
    const refreshes = fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/auth/refresh"));
    expect(refreshes).toHaveLength(1);
  });

  it("ends the session when the refresh cookie is rejected", async () => {
    const { apiFetch, ApiError, SIGNED_OUT_EVENT } = await load();
    const onSignedOut = vi.fn();
    vi.stubGlobal("window", { dispatchEvent: onSignedOut });
    fetchMock.mockResolvedValue(json({ detail: "Not signed in" }, 401));
    await expect(apiFetch("/objectives")).rejects.toBeInstanceOf(ApiError);
    expect(onSignedOut).toHaveBeenCalledOnce();
    expect(onSignedOut.mock.calls[0]![0].type).toBe(SIGNED_OUT_EVENT);
  });

  it("keeps the session when the refresh fails for a non-401 reason", async () => {
    const { apiFetch } = await load();
    const onSignedOut = vi.fn();
    vi.stubGlobal("window", { dispatchEvent: onSignedOut });
    fetchMock
      .mockResolvedValueOnce(json({ detail: "Not signed in" }, 401))
      .mockResolvedValueOnce(json({ detail: "boom" }, 502));
    await expect(apiFetch("/objectives")).rejects.toMatchObject({ status: 502 });
    expect(onSignedOut).not.toHaveBeenCalled();
  });

  it("does not refresh for the auth endpoints themselves", async () => {
    const { apiFetch } = await load();
    fetchMock.mockResolvedValueOnce(json({ detail: "Incorrect email or password" }, 401));
    await expect(
      apiFetch("/auth/login", { method: "POST", json: {}, auth: false }),
    ).rejects.toThrow("Incorrect email or password");
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("turns a validation error list into a readable message", async () => {
    const { apiFetch } = await load();
    fetchMock.mockResolvedValueOnce(json({ detail: [{ msg: "bad" }] }, 422));
    await expect(apiFetch("/objectives")).rejects.toThrow("Some of the details are not valid.");
  });
});
