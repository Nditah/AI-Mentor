import { clerkFrontendApi } from "@/lib/clerk";

function origin(url: string): string | null {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

/** Security-Compliance §8.4: nonce-based scripts, no inline script, no framing. */
export function contentSecurityPolicy(nonce: string): string {
  const dev = process.env.NODE_ENV === "development";
  const api = origin(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
  const learner = origin(process.env.NEXT_PUBLIC_LEARNER_URL || "http://localhost:3000");
  const clerk = clerkFrontendApi();
  const clerkHosts = clerk ? [`https://${clerk}`, "https://challenges.cloudflare.com"] : [];
  const directives: Record<string, (string | null | false)[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'", dev && "'unsafe-eval'", ...clerkHosts],
    "connect-src": ["'self'", api, learner, ...clerkHosts, dev && "ws:"],
    "img-src": ["'self'", "data:", "blob:", clerk ? "https://img.clerk.com" : null],
    "style-src": ["'self'", "'unsafe-inline'"],
    "font-src": ["'self'", "data:"],
    "frame-src": clerkHosts.length ? clerkHosts : ["'none'"],
    "worker-src": ["'self'", "blob:"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'", api, ...clerkHosts],
    "frame-ancestors": ["'none'"],
  };
  const policy = Object.entries(directives).map(
    ([name, values]) => `${name} ${values.filter(Boolean).join(" ")}`,
  );
  if (api?.startsWith("https://")) policy.push("upgrade-insecure-requests");
  return policy.join("; ");
}
