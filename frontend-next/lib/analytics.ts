/**
 * Analytics-ready event layer for KAVACH.
 *
 * No analytics provider is installed in this project, so nothing is loaded and
 * no third-party script is introduced here. Events are pushed to `window.dataLayer`
 * when a tag manager is later installed, and are otherwise a safe no-op.
 *
 * This keeps the semantic event names in place so that measurement can be wired
 * up later without touching the components that emit them.
 */

export type KavachEventName =
  | 'services_page_view'
  | 'consultation_page_view'
  | 'consultation_booking_click'
  | 'pooja_2100_booking_click'
  | 'pooja_5100_booking_click'
  | 'pooja_11000_booking_click'
  | 'services_cta_view'
  | 'services_cta_click';

export interface KavachEventPayload {
  [key: string]: string | number | boolean | undefined;
}

declare global {
  interface Window {
    dataLayer?: Array<Record<string, unknown>>;
  }
}

/**
 * Record a semantic KAVACH event.
 *
 * Provider-free: it never loads a script, never sends a network request of its
 * own and never throws. Analytics wiring is PENDING owner approval.
 */
export function trackEvent(name: KavachEventName, payload: KavachEventPayload = {}): void {
  if (typeof window === 'undefined') return;
  try {
    const event = { event: name, ...payload };
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(event);
  } catch {
    // Measurement must never break the page.
  }
}
