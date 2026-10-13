const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";

export const clerkEnabled = publishableKey.length > 0;
export const devAuth = process.env.NEXT_PUBLIC_DEV_AUTH === "true";

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
