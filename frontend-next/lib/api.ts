import type { PanchangResult } from './panchang';
﻿import { BirthDetails, DrishtiReading, KundliData, PlaceSuggestion } from './types';

const PRODUCTION_ORIGIN = 'https://drishti-5j3u.onrender.com';
const LOCAL_API_PORT = 8000;

function resolveOrigin(): string {
  if (typeof window !== 'undefined' && window.location?.hostname) {
    const host = window.location.hostname;
    const isLocal =
      host === 'localhost' ||
      host === '127.0.0.1' ||
      host === '0.0.0.0' ||
      /^[0-9]{1,3}([.][0-9]{1,3}){3}$/.test(host);
    if (isLocal) return `http://${host}:${LOCAL_API_PORT}`;
  }
  return PRODUCTION_ORIGIN;
}

export const API_ORIGIN = resolveOrigin();

export const API_BASE = `${API_ORIGIN}/api`;

interface RawChart {
  status: string;
  reason?: string | null;
  ascendant?: { sign: string; degree?: number };
  ascendant_sign?: string | null;
  planets?: Array<{ name: string; sign: string; house: number; degree?: number }>;
  extra_planets?: Array<{ name: string; sign: string; house: number; degree?: number }>;
  houses?: Array<{ number: number; sign: string }>;
}

interface RawArea {
  area: string;
  hook?: string;
  description: string;
  potential_impact?: string;
  mindful_of?: string[];
  takeaway?: string;
}

interface RawInterpretation {
  status: 'success' | 'error';
  message?: string;
  attention: RawArea;
  protect: RawArea;
  danger: RawArea;
  chart?: RawChart;
  timing?: {
    current: PublicCaution | null;
    upcoming: PublicCaution[];
  };
}

interface PublicCaution {
  start_date: string;
  end_date: string;
  level: string;
  area: string;
  title: string;
  guidance: string;
}

const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const RETRYABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);
const DEFAULT_TIMEOUT_MS = 45000;
const DEFAULT_RETRY_DELAYS_MS = [2000, 4000];

interface RequestOptions {
  timeoutMs?: number;
  retryDelaysMs?: number[];
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchOnce(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

function isTransientError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === 'AbortError') return true;
  if (error instanceof TypeError) return true;
  if (error instanceof Error && error.message === 'NETWORK_ERROR') return true;
  return false;
}

async function request<T>(path: string, init?: RequestInit, options: RequestOptions = {}): Promise<T> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const retryDelaysMs = options.retryDelaysMs ?? DEFAULT_RETRY_DELAYS_MS;
  const maxAttempts = retryDelaysMs.length + 1;
  let lastError: unknown;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      const response = await fetchOnce(`${API_BASE}${path}`, init ?? {}, timeoutMs);
      if (!response.ok) {
        const text = await response.text().catch(() => '');
        const retryable = RETRYABLE_STATUS.has(response.status);
        if (retryable && attempt < maxAttempts - 1) {
          lastError = new Error(text || `Request failed: ${response.status}`);
          await delay(retryDelaysMs[Math.min(attempt, retryDelaysMs.length - 1)]);
          continue;
        }
        throw new Error(text || `Request failed: ${response.status}`);
      }
      return (await response.json()) as T;
    } catch (error) {
      const retryable = isTransientError(error);
      if (retryable && attempt < maxAttempts - 1) {
        lastError = error;
        await delay(retryDelaysMs[Math.min(attempt, retryDelaysMs.length - 1)]);
        continue;
      }
      throw error instanceof Error ? error : new Error('Request failed');
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Request failed');
}

export function wakeBackend(): void {
  try {
    fetch(`${API_BASE}/health`, { method: 'GET', cache: 'no-store' }).catch(() => {});
  } catch {
    // Silent wake-up only ΓÇö never block navigation.
  }
}

export interface PanchangQuery {
  date: string;
  latitude: number;
  longitude: number;
  timezone: string;
  label?: string;
}

export async function getPanchang(query: PanchangQuery): Promise<PanchangResult> {
  const params = new URLSearchParams({
    date: query.date,
    latitude: String(query.latitude),
    longitude: String(query.longitude),
    timezone: query.timezone,
    label: query.label ?? '',
  });
  return request<PanchangResult>(`/panchang?${params.toString()}`);
}

function adaptKundli(chart: RawChart): KundliData {
  const planets = [...(chart.planets || []), ...(chart.extra_planets || [])];
  return {
    ascendantSign: chart.ascendant?.sign || chart.ascendant_sign || 'ΓÇö',
    ascendantDegree: chart.ascendant?.degree === undefined ? undefined : `${chart.ascendant.degree.toFixed(2)}┬░`,
    houses: Array.from({ length: 12 }, (_, index) => {
      const houseNumber = index + 1;
      const house = chart.houses?.find((item) => item.number === houseNumber);
      return { houseNumber, sign: house?.sign || 'ΓÇö', signNumber: Math.max(1, signNames.indexOf(house?.sign || '') + 1), planets: planets.filter((planet) => planet.house === houseNumber).map((planet) => planet.name) };
    }),
    planetaryPositions: planets.map((planet) => ({ planet: planet.name as never, house: planet.house, sign: planet.sign, degree: planet.degree === undefined ? undefined : `${planet.degree.toFixed(2)}┬░` })),
  };
}

function adaptArea(raw: RawArea, id: 'attention' | 'protect' | 'danger', stepNumber: string, environmentalTheme: 'light' | 'mixed' | 'deep-crimson') {
  return {
    id, stepNumber,
    label: id === 'attention' ? 'ATTENTION AREA' : id === 'protect' ? 'PROTECT THIS AREA' : 'DANGER AREA',
    title: raw.area,
    subtitle: id === 'attention' ? 'Where natural instinct needs conscious calibration' : id === 'protect' ? 'Know where to stop' : 'What should not be ignored',
    quote: '',
    summary: raw.description,
    body: raw.potential_impact ? [raw.potential_impact] : [],
    watchFor: { primary: raw.mindful_of?.[0] || '', points: raw.mindful_of?.slice(1) || [] },
    environmentalTheme,
  };
}

export interface PlaceSearchOutcome {
  results: PlaceSuggestion[];
  /** True when the location service is temporarily unavailable (not "no matches"). */
  unavailable: boolean;
}

// Shared autocomplete guard: identical normalized queries are answered from a
// short-lived memo and concurrent identical lookups share one request, so fast
// typing cannot fire duplicate upstream work or race stale results.
const PLACE_LOOKUP_TTL_MS = 20_000;
const placeLookups = new Map<string, { at: number; outcome: PlaceSearchOutcome }>();
const placeInFlight = new Map<string, Promise<PlaceSearchOutcome>>();

export const api = {
  /**
   * Place autocomplete. Distinguishes "no matches" from "service unavailable" so
   * the dropdown never looks empty as though a city did not exist.
   */
  async searchPlacesDetailed(query: string): Promise<PlaceSearchOutcome> {
    const trimmed = query.trim();
    if (trimmed.length < 3) return { results: [], unavailable: false };
    const key = trimmed.toLowerCase().replace(/\s+/g, ' ');

    const memo = placeLookups.get(key);
    if (memo && Date.now() - memo.at < PLACE_LOOKUP_TTL_MS) return memo.outcome;
    const inFlight = placeInFlight.get(key);
    if (inFlight) return inFlight;

    const task = (async (): Promise<PlaceSearchOutcome> => {
      try {
        const response = await request<{ results?: Array<{ display: string; lat: number; lon: number }> }>(
          `/places/search?q=${encodeURIComponent(trimmed)}`,
          undefined,
          { timeoutMs: 8000, retryDelaysMs: [] },
        );
        const results = (response.results || []).map((place, index) => {
          const parts = place.display.split(',').map((part) => part.trim());
          return {
            id: `${place.lat}-${place.lon}-${index}`,
            name: parts[0] || place.display,
            region: parts[1] || '',
            country: parts.slice(2).join(', ') || '',
            coordinates: { lat: place.lat, lng: place.lon },
          };
        });
        const outcome: PlaceSearchOutcome = { results, unavailable: false };
        placeLookups.set(key, { at: Date.now(), outcome });
        return outcome;
      } catch {
        // 503 (upstream geocoder unavailable) or a network failure: report it as
        // temporarily unavailable instead of pretending there are no cities.
        const outcome: PlaceSearchOutcome = { results: [], unavailable: true };
        placeLookups.set(key, { at: Date.now(), outcome });
        return outcome;
      } finally {
        placeInFlight.delete(key);
      }
    })();

    placeInFlight.set(key, task);
    return task;
  },

  async searchPlaces(query: string): Promise<PlaceSuggestion[]> {
    return (await api.searchPlacesDetailed(query)).results;
  },

  async calculateChart(birthDetails: BirthDetails) {
    const raw = await request<RawChart>('/chart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    if (raw.status === 'ERROR') throw new Error(raw.reason || 'Chart calculation failed.');
    return { kundli: adaptKundli(raw), ascendant: raw.ascendant?.sign || raw.ascendant_sign || 'ΓÇö' };
  },

  async getInterpretation(birthDetails: BirthDetails): Promise<DrishtiReading> {
    const raw = await request<RawInterpretation>('/interpretation', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    if (raw.status === 'error') throw new Error(raw.message || 'Unable to complete your reading.');
    const chart = raw.chart || await request<RawChart>('/chart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    return {
      id: `reading-${Date.now()}`, createdAt: new Date().toISOString(), birthDetails,
      ascendant: chart.ascendant?.sign || chart.ascendant_sign || 'ΓÇö',
      headline: 'Know what deserves your attention.',
      overview: 'A clear view of the areas where awareness, boundaries, and care can make the greatest difference.',
      kundli: adaptKundli(chart),
      attentionArea: adaptArea(raw.attention, 'attention', '01', 'light'),
      protectArea: adaptArea(raw.protect, 'protect', '02', 'mixed'),
      dangerArea: adaptArea(raw.danger, 'danger', '03', 'deep-crimson'),
      cautionPeriods: [
        ...(raw.timing?.current ? [{ ...mapCaution(raw.timing.current), isCurrent: true }] : []),
        ...(raw.timing?.upcoming || []).map(mapCaution),
      ],
      takeaway: { title: 'YOUR TAKEAWAY', thesis: 'Awareness is your highest-leverage advantage.', guidance: 'Stay attentive to the areas highlighted in your reading. Clear boundaries and deliberate pacing can help you handle them with greater confidence.', anchorWords: ['Awareness', 'Boundaries', 'Deliberate pacing'] },
    };
  },
};

function mapCaution(item: PublicCaution) {
  return {
    id: `${item.start_date}-${item.end_date}-${item.area}`,
    period: `${item.start_date} ΓÇö ${item.end_date}`,
    intensity: item.level === 'high' ? 'critical' as const : 'heightened' as const,
    title: item.title,
    description: item.guidance,
    focus: item.area,
  };
}
