import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse, type NextFetchEvent, type NextRequest } from "next/server";
import { clerkEnabled, contentSecurityPolicy } from "@/lib/csp";

const isPublic = createRouteMatcher(["/", "/sign-in(.*)", "/sign-up(.*)"]);

// Security-Compliance §8.4: a new policy runs in Report-Only for a week before it is enforced.
const responseHeader =
  process.env.CSP_REPORT_ONLY === "true" ? "Content-Security-Policy-Report-Only" : "Content-Security-Policy";

function secured(request: NextRequest) {
  const nonce = btoa(crypto.randomUUID());
  const policy = contentSecurityPolicy(nonce);
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", policy);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set(responseHeader, policy);
  return response;
}

const withClerk = clerkMiddleware(async (auth, request) => {
  if (!isPublic(request)) await auth.protect();
  return secured(request);
});

export default function proxy(request: NextRequest, event: NextFetchEvent) {
  return clerkEnabled ? withClerk(request, event) : secured(request);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg|.*\\.(?:png|jpg|jpeg|svg|ico|webp|woff2?)$).*)"],
};
