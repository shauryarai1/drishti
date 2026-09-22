/**
 * Open-redirect protection.
 *
 * Only same-origin KAVACH paths are ever used as post-auth destinations, so a
 * crafted ?next= value can never bounce a user to an external site.
 */

const SAFE_PATHS = [
  '/account',
  '/history',
  '/admin',
  '/kundli',
  '/daily',
  '/your-week',
  '/life-summary',
  '/reading',
  '/results',
  '/ask',
  '/panchang',
] as const;

export const DEFAULT_AUTH_DESTINATION = '/account';

export function isSafeInternalPath(raw: string | null | undefined): boolean {
  if (!raw) return false;
  if (!raw.startsWith('/')) return false;
  if (raw.startsWith('//')) return false; // protocol-relative
  if (raw.includes('\\') || raw.includes('\n') || raw.includes('\r')) return false;
  if (/^\/[^/]*:/.test(raw)) return false; // "/javascript:..." style schemes

  const path = raw.split(/[?#]/)[0];
  if (path === '/') return true;
  return SAFE_PATHS.some((allowed) => path === allowed || path.startsWith(`${allowed}/`));
}

export function safeNextPath(raw: string | null | undefined): string {
  if (!isSafeInternalPath(raw)) return DEFAULT_AUTH_DESTINATION;
  return raw as string;
}

/** Builds a guarded /login link that preserves the current internal location. */
export function loginHref(nextPath: string | null | undefined): string {
  const next = safeNextPath(nextPath);
  return `/login?next=${encodeURIComponent(next)}`;
}
