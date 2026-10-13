import type { NextConfig } from "next";

const deployEnv = process.env.DEPLOY_ENV || process.env.VERCEL_ENV || "";
const production = deployEnv === "production";
const hosted = production || deployEnv === "preview" || deployEnv === "staging";

if (hosted && process.env.NEXT_PUBLIC_DEV_AUTH === "true") {
  throw new Error("NEXT_PUBLIC_DEV_AUTH=true is refused in a hosted build.");
}

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ...(production
    ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }]
    : []),
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async redirects() {
    return [
      { source: "/platform/paths", destination: "/paths", permanent: true },
      { source: "/sign-in", destination: "/login", permanent: false },
      { source: "/sign-up", destination: "/register", permanent: false },
    ];
  },
};

export default nextConfig;
