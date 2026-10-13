"use client";

import { useAuth } from "@clerk/nextjs";
import { setTokenSource } from "@/lib/auth";

/** Hands Clerk's session token to the API client; children wait until Clerk has loaded. */
export function AuthBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, getToken } = useAuth();
  setTokenSource(isLoaded ? () => getToken() : null);
  return isLoaded ? <>{children}</> : null;
}
