/** @type {import('next').NextConfig} */
// Content-Security-Policy is built from what KAVACH actually loads:
//   - same-origin assets
//   - Google Fonts (stylesheets + font files)
//   - Supabase (auth + saved readings) and the Render FastAPI origin
//   - localhost origins so local development keeps working
// Framework-required exceptions: Next.js injects inline bootstrap scripts and
// inline styles, so 'unsafe-inline' is needed for scripts and styles, and
// 'unsafe-eval' is required by the dev/HMR runtime. No third-party script
// origins are permitted.
const SUPABASE_ORIGIN = 'https://*.supabase.co';
const API_ORIGIN = 'https://drishti-5j3u.onrender.com';

const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com data:",
  "img-src 'self' data: blob:",
  `connect-src 'self' ${SUPABASE_ORIGIN} ${API_ORIGIN} http://localhost:8000 http://127.0.0.1:8000 ws://localhost:3000 ws://127.0.0.1:3000`,
  "frame-src 'none'",
].join('; ');

const securityHeaders = [
  { key: 'Content-Security-Policy', value: csp },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), payment=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
];

const nextConfig = {
  reactStrictMode: true,
  // Source maps are intentionally NOT shipped to the browser in production.
  productionBrowserSourceMaps: false,
  images: {
    unoptimized: true,
  },
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};

module.exports = nextConfig;
