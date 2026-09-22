/**
 * Short-lived pending-form storage.
 *
 * Lets a guest fill a product form, hit the auth gate, and continue after
 * signing in WITHOUT retyping their details.
 *
 * Rules:
 *   - sessionStorage only (dies with the tab), namespaced per product.
 *   - ONLY the allow-listed birth fields are ever stored. No credentials, no
 *     tokens, no provider keys, no account identifiers.
 *   - Nothing is ever put in the URL.
 *   - Restored data is validated before use, and entries expire.
 *   - Cleared as soon as the pending form has been consumed.
 */

export type PendingProduct = 'kundli' | 'reading' | 'life_summary' | 'your_week' | 'compatibility';

const KEY_PREFIX = 'kavach_pending_v1';
const MAX_AGE_MS = 30 * 60 * 1000; // 30 minutes

export interface PendingBirthForm {
  name?: string;
  date: string;
  time: string;
  place: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
  // Your Week also carries the forecast window and its own location.
  startDate?: string;
  forecastPlace?: string;
  forecastLatitude?: number;
  forecastLongitude?: number;
  forecastTimezone?: string;
  // Compatibility carries two complete birth profiles, kept separate.
  bride_name?: string;
  bride_date?: string;
  bride_time?: string;
  bride_place?: string;
  bride_latitude?: number;
  bride_longitude?: number;
  bride_timezone?: string;
  groom_name?: string;
  groom_date?: string;
  groom_time?: string;
  groom_place?: string;
  groom_latitude?: number;
  groom_longitude?: number;
  groom_timezone?: string;
}

const NUMERIC_FIELDS = new Set([
  'latitude',
  'longitude',
  'forecastLatitude',
  'forecastLongitude',
  'bride_latitude',
  'bride_longitude',
  'groom_latitude',
  'groom_longitude',
]);

/** Fields that must be present for a restored form to be usable. */
const REQUIRED_FIELDS: Record<PendingProduct, string[]> = {
  kundli: ['date', 'time', 'place'],
  reading: ['date', 'time', 'place'],
  life_summary: ['date', 'time', 'place'],
  your_week: ['date', 'time', 'place'],
  compatibility: ['bride_date', 'bride_time', 'bride_place',
                  'groom_date', 'groom_time', 'groom_place'],
};

const ALLOWED_FIELDS: Record<PendingProduct, (keyof PendingBirthForm)[]> = {
  kundli: ['name', 'date', 'time', 'place', 'latitude', 'longitude', 'timezone'],
  reading: ['date', 'time', 'place', 'latitude', 'longitude', 'timezone'],
  life_summary: ['date', 'time', 'place', 'latitude', 'longitude', 'timezone'],
  // Dedicated key: Your Week must never share KAVACH Reading's pending state.
  your_week: ['date', 'time', 'place', 'latitude', 'longitude', 'timezone',
              'startDate', 'forecastPlace', 'forecastLatitude', 'forecastLongitude',
              'forecastTimezone'],
  // Dedicated key: compatibility is its own product with two profiles.
  compatibility: ['bride_name', 'bride_date', 'bride_time', 'bride_place',
                  'bride_latitude', 'bride_longitude', 'bride_timezone',
                  'groom_name', 'groom_date', 'groom_time', 'groom_place',
                  'groom_latitude', 'groom_longitude', 'groom_timezone'],
};

function storageKey(product: PendingProduct): string {
  return `${KEY_PREFIX}:${product}`;
}

function store(): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

/** Keep only the allow-listed fields, with the expected primitive types. */
function pick(product: PendingProduct, data: Record<string, unknown>): PendingBirthForm | null {
  const out: Record<string, unknown> = {};
  for (const field of ALLOWED_FIELDS[product]) {
    const value = data[field];
    if (value === undefined || value === null) continue;
    if (NUMERIC_FIELDS.has(field as string)) {
      const numeric = Number(value);
      if (Number.isFinite(numeric)) out[field] = numeric;
      continue;
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed) out[field] = trimmed.slice(0, 200);
    }
  }

  // A restored form is only usable when its required fields are present.
  if (REQUIRED_FIELDS[product].some((field) => typeof out[field] !== 'string')) {
    return null;
  }
  return out as unknown as PendingBirthForm;
}

export function savePendingForm(product: PendingProduct, data: Record<string, unknown>): void {
  const target = store();
  if (!target) return;
  const payload = pick(product, data);
  if (!payload) return;
  try {
    target.setItem(storageKey(product), JSON.stringify({ savedAt: Date.now(), data: payload }));
  } catch {
    // Storage may be unavailable or full; the guest simply retypes the form.
  }
}

export function readPendingForm(product: PendingProduct): PendingBirthForm | null {
  const target = store();
  if (!target) return null;
  try {
    const raw = target.getItem(storageKey(product));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { savedAt?: number; data?: Record<string, unknown> };
    if (!parsed || typeof parsed.savedAt !== 'number' || !parsed.data) {
      clearPendingForm(product);
      return null;
    }
    if (Date.now() - parsed.savedAt > MAX_AGE_MS) {
      clearPendingForm(product);
      return null;
    }
    return pick(product, parsed.data);
  } catch {
    clearPendingForm(product);
    return null;
  }
}

/** Read once and clear, so a stale form cannot generate a result later. */
export function takePendingForm(product: PendingProduct): PendingBirthForm | null {
  const value = readPendingForm(product);
  clearPendingForm(product);
  return value;
}

export function clearPendingForm(product: PendingProduct): void {
  const target = store();
  if (!target) return;
  try {
    target.removeItem(storageKey(product));
  } catch {
    // Ignore: nothing depends on the removal succeeding.
  }
}
