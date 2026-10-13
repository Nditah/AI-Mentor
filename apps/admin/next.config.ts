import type { NextConfig } from "next";

const deployEnv = process.env.DEPLOY_ENV || process.env.VERCEL_ENV || "";
const production = deployEnv === "production";
const hosted = production || deployEnv === "preview" || deployEnv === "staging";

if (hosted && process.env.NEXT_PUBLIC_DEV_AUTH === "true") {
  throw new Error("NEXT_PUBLIC_DEV_AUTH=true is refused in a hosted build.");
}
if (hosted && !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
  throw new Error("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required in a hosted build.");
}

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Robots-Tag", value: "noindex, nofollow" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ...(production
    ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }]
    : []),
];

const studio = process.env.NEXT_PUBLIC_STUDIO_URL || "http://localhost:3004";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async redirects() {
    const moved = [
      "library",
      "review",
      "curriculum",
      "taxonomy",
      "graph",
      "generate",
      "challenges",
      "catalog",
      "studio",
    ];
    return moved.flatMap((route) => [
      { source: `/${route}`, destination: `${studio}/${route}`, permanent: false },
      { source: `/${route}/:path*`, destination: `${studio}/${route}/:path*`, permanent: false },
    ]);
  },
};

export default nextConfig;
