const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";

export const clerkEnabled = publishableKey.length > 0;

/** The Clerk Frontend API host is encoded in the publishable key: pk_<env>_<base64(host$)>. */
export function clerkFrontendApi(key = publishableKey): string | null {
  const encoded = key.split("_")[2];
  if (!encoded) return null;
  try {
    return atob(encoded).replace(/\$$/, "") || null;
  } catch {
    return null;
  }
}

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
  const clerk = clerkFrontendApi();
  const clerkHosts = clerk ? [`https://${clerk}`, "https://challenges.cloudflare.com"] : [];
  const directives: Record<string, (string | null | false)[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'", dev && "'unsafe-eval'", ...clerkHosts],
    "connect-src": ["'self'", api, ...clerkHosts, dev && "ws:"],
    "img-src": ["'self'", "data:", "blob:", clerk ? "https://img.clerk.com" : null],
    "style-src": ["'self'", "'unsafe-inline'"],
    "font-src": ["'self'", "data:"],
    "frame-src": clerkHosts.length ? clerkHosts : ["'none'"],
    "worker-src": ["'self'", "blob:"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
  };
  const policy = Object.entries(directives).map(
    ([name, values]) => `${name} ${values.filter(Boolean).join(" ")}`,
  );
  if (api?.startsWith("https://")) policy.push("upgrade-insecure-requests");
  return policy.join("; ");
}
