import { siteConfig } from "@/config/site";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Thin typed wrapper over fetch. Errors follow the FastAPI boilerplate shape: { detail: string }.
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${siteConfig.apiUrl}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init.headers },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(response.status, body?.detail ?? response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
