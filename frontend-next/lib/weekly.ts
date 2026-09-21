import { API_BASE, api } from './api';
import type { PlaceSuggestion } from './types';

// "Your Week" public API client. Types mirror ONLY the customer-safe payload:
// no private methodology fields exist on the frontend at all.

export interface WeeklyPeriod {
  label: string;
  start: string;
  end: string;
  afterTime: string;
  headline: string;
  guidance: string;
  tone: 'supportive' | 'caution' | 'strong_caution' | 'personal';
}

export interface WeeklyDay {
  date: string;
  headline: string;
  summary: string;
  periods: WeeklyPeriod[];
}

export interface WeeklyHighlight {
  label: string;
  date: string;
  time: string;
  text: string;
}

export interface WeeklyForecast {
  startDate: string;
  endDate: string;
  timezone: string;
  weekSummary: string;
  highlights: WeeklyHighlight[];
  days: WeeklyDay[];
}

export interface WeeklyPlace {
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface WeeklyRequest {
  birth: { date: string; time: string; place: string; latitude: number; longitude: number; timezone: string };
  forecast: { startDate: string; place: string; latitude: number; longitude: number; timezone: string };
}

export async function fetchWeekly(payload: WeeklyRequest): Promise<WeeklyForecast> {
  const response = await fetch(`${API_BASE}/weekly`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || (body as { status?: string }).status === 'error') {
    const message = (body as { message?: string }).message;
    throw new Error(message || "We couldn't prepare your week with those details.");
  }
  return body as WeeklyForecast;
}

/** Searches places through the EXISTING KAVACH search API.
 *
 * PlaceSuggestion shape: { id, name, region, country, coordinates: { lat, lng } }
 * The backend requires at least 3 characters, so callers must debounce.
 */
export async function searchWeeklyPlaces(query: string, timezone = 'Asia/Kolkata'): Promise<WeeklyPlace[]> {
  const trimmed = query.trim();
  if (trimmed.length < 3) return [];
  let results: PlaceSuggestion[] = [];
  try {
    results = await api.searchPlaces(trimmed);
  } catch {
    return [];
  }
  if (!Array.isArray(results)) return [];
  return results
    .map((item) => {
      const lat = Number(item?.coordinates?.lat);
      const lng = Number(item?.coordinates?.lng);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
      const label = [item.name, item.region, item.country].filter(Boolean).join(', ');
      return { label: label || item.name, latitude: lat, longitude: lng, timezone };
    })
    .filter((item): item is WeeklyPlace => item !== null);
}

/** Blur fallback: first match only (kept for compatibility). */
export async function resolveWeeklyPlace(query: string, timezone = 'Asia/Kolkata'): Promise<WeeklyPlace | null> {
  const places = await searchWeeklyPlaces(query, timezone);
  return places[0] ?? null;
}
