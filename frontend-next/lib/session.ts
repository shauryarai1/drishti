'use client';

/**
 * Non-identifying visitor session id.
 *
 * Used only to group multiple product actions from the same browser session for
 * the owner archive as "Guest". It is a random value held in sessionStorage: it
 * is not derived from IP, device, or any fingerprinting signal, and it carries
 * no personal information.
 */

const KEY = 'kavach_visitor_session';

function randomId(): string {
  try {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  } catch {
    /* fall through */
  }
  return `s-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
}

export function visitorSessionId(): string {
  if (typeof window === 'undefined') return '';
  try {
    const existing = window.sessionStorage.getItem(KEY);
    if (existing) return existing;
    const created = randomId();
    window.sessionStorage.setItem(KEY, created);
    return created;
  } catch {
    return '';
  }
}
