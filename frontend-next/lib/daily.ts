import { API_BASE } from './api';

// Daily Prediction API client. Origin comes from the host-aware API_BASE, so
// localhost / 127.0.0.1 / LAN / deployed resolve exactly as the rest of KAVACH.

export type DailyStatus = 'GOOD' | 'NEUTRAL' | 'CAUTION';

export interface DailyCategory {
  status: DailyStatus;
  reason: string;
}

export interface DailyCard {
  sign: string;
  /** Authoritative active houses from the Nakshatra lord's ruled Rashi/Rashis. */
  activeHouses: number[];
  /** Backwards-compatible first active house. */
  activeHouse: number;
  title: string;
  /** ONE integrated prediction based on the active house or houses. */
  pattern: string;
  categories: { love: DailyCategory; health: DailyCategory; career: DailyCategory };
  bestColour: string | null;
  earlierTitle?: string;
  isPersonal: boolean;
}

export interface DailyMoon {
  date: string;
  sunrise: string;
  sunriseLocal: string;
  longitude: number;
  rashi: string;
}

export interface CurrentMoon {
  rashi: string;
  longitude: number;
  asOf: string;
}

export interface DailyResponse {
  status: string;
  asOf: { timestamp: string; timezone: string };
  dailyMoon: DailyMoon;
  currentMoon: CurrentMoon;
  natalMoon: string | null;
  signs: DailyCard[];
  basis: string;
  /** Transparent context for the Nakshatra-lord rulership calculation. */
  nakshatra?: {
    name: string;
    lord: string;
    ruledRashis: string[];
    mode: string;
    navtara: string;
    navtaraTone: { tone?: string; guidance?: string };
  };
}

export interface DailyRequest {
  latitude: number;
  longitude: number;
  timezone: string;
  /** The user's LOCAL calendar date (YYYY-MM-DD). Authoritative for the day. */
  date?: string;
  /** Legacy only; ignored by the active Daily methodology. */
  natal_moon?: string;
  /** Legacy only; ignored by the active Daily methodology. */
  natal_nakshatra?: string;
}

export async function fetchDaily(payload: DailyRequest): Promise<DailyResponse> {
  const response = await fetch(`${API_BASE}/daily`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // The reading is date/time-sensitive: never let a cached response serve a
    // previous day's reading.
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || (body as { status?: string }).status === 'error') {
    throw new Error('Daily prediction unavailable');
  }
  return body as DailyResponse;
}

export const MOON_SIGNS = [  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const;

/**
 * Reuses the city already chosen elsewhere in KAVACH (Panchang storage key).
 *
 * Each city carries its own IANA timezone: the Daily Moon rashi is the Moon at
 * LOCAL sunrise for that location, so the timezone must match the coordinates.
 * A single hardcoded zone anchored the wrong calendar day / Moon for every
 * non-Indian city.
 */
export const DAILY_CITIES = [
  { label: 'New Delhi, India', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' },
  { label: 'Mumbai, India', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { label: 'Bengaluru, India', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  { label: 'Chennai, India', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { label: 'Kolkata, India', latitude: 22.5726, longitude: 88.3639, timezone: 'Asia/Kolkata' },
  { label: 'Hyderabad, India', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  { label: 'London, United Kingdom', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { label: 'New York, United States', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { label: 'Dubai, UAE', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { label: 'Singapore', latitude: 1.3521, longitude: 103.8198, timezone: 'Asia/Singapore' },
  { label: 'Sydney, Australia', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
];
