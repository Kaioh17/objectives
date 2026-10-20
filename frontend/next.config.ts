import type { NextConfig } from "next";

const isProduction = process.env.NEXT_PUBLIC_APP_ENV === "production";

// Baseline hardening. Add a Content-Security-Policy (nonce-based, via proxy) once you know your origins.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" }, // relax if the app must be embedded
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  // HSTS only where HTTPS is guaranteed
  ...(isProduction
    ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }]
    : []),
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Docker/self-hosting switch; Dockerfile sets BUILD_STANDALONE=true
  output: process.env.BUILD_STANDALONE === "true" ? "standalone" : undefined,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
