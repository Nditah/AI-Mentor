import { sessionToken } from "@/lib/auth";
import { clerkEnabled } from "@/lib/csp";
import { apiBase, devAuth } from "@/lib/utils";
import { useStudio } from "@/stores/studio";

export class ApiError extends Error {
  status: number;
  traceId?: string;

  constructor(status: number, message: string, traceId?: string) {
    super(message);
    this.status = status;
    this.traceId = traceId;
  }
}

type Problem = { detail?: string; trace_id?: string; errors?: { path: string; message: string }[] };

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = await sessionToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  } else if (devAuth && !clerkEnabled) {
    const devUser = useStudio.getState().devUserId;
    if (devUser) headers.set("X-Dev-User-Id", devUser);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    let traceId: string | undefined;
    try {
      const problem = (await response.json()) as Problem;
      if (problem.detail) detail = problem.detail;
      if (problem.errors?.length) detail = problem.errors.map((item) => item.message).join(" ");
      traceId = problem.trace_id;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail, traceId);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function apiStream(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = await sessionToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  } else if (devAuth && !clerkEnabled) {
    const devUser = useStudio.getState().devUserId;
    if (devUser) headers.set("X-Dev-User-Id", devUser);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "text/event-stream");
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    let traceId: string | undefined;
    try {
      const problem = (await response.json()) as Problem;
      if (problem.detail) detail = problem.detail;
      if (problem.errors?.length) detail = problem.errors.map((item) => item.message).join(" ");
      traceId = problem.trace_id;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail, traceId);
  }
  return response;
}

export async function* readSse(response: Response): AsyncGenerator<Record<string, unknown>> {
  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      yield JSON.parse(line.slice(6)) as Record<string, unknown>;
    }
  }
}
