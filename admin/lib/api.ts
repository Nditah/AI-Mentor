export const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const studioUrl = process.env.NEXT_PUBLIC_STUDIO_URL || "http://localhost:3000";
export const devAuth = process.env.NEXT_PUBLIC_DEV_AUTH === "true";

const key = "ai-mentor-admin-user";

export function devUser(): string {
  if (typeof window === "undefined") return "demo-admin";
  return window.localStorage.getItem(key) || "demo-admin";
}

export function setDevUser(id: string) {
  window.localStorage.setItem(key, id);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (devAuth) headers.set("X-Dev-User-Id", devUser());
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}
