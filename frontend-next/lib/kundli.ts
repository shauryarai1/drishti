import { API_BASE } from './api';
import { authHeaders } from './authHeaders';
import type { BirthDetails, KundliData } from './types';

// Kundli Generator API client.
//
// Kept in its own module so the shared lib/api.ts exports are never at risk
// (a previous rewrite there silently dropped exports). Origin comes from the
// host-aware API_BASE, so localhost / 127.0.0.1 / LAN / deployed all resolve
// exactly as the rest of the app does.

export interface KundliBirth {
  name: string;
  date: string;
  time: string;
  place: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface KundliSummary {
  lagna: string;
  lagnaRashi: string;
  moonRashi: string;
  sunRashi: string;
  nakshatra: string;
  pada: number;
  ascendantNakshatra: string;
  ascendantPada: number;
  ascendantNakshatraLord: string;
  paksha: string;
  tithi: string;
}

export interface KundliPlanet {
  planet: string;
  longitude: number;
  rashi: string;
  degree: number;
  house: number;
  nakshatra: string;
  pada: number;
  nakshatraLord: string;
  motion: string;
}

export interface KundliHouse {
  number: number;
  rashi: string;
  cuspLongitude: number;
}

export interface KundliChart {
  ascendant: {
    rashi: string;
    degree: number;
    longitude: number;
    nakshatra: string;
    pada: number;
    nakshatraLord: string;
  };
  houses: KundliHouse[];
  planets: KundliPlanet[];
}

export interface KundliPanchang {
  vara: string;
  tithi: string;
  paksha: string;
  nakshatra: string;
  pada: number;
  yoga: string;
  karana: string;
  sunRashi: string;
  moonRashi: string;
}

export interface KundliMahadasha {
  lord: string;
  start: string;
  end: string;
  years: number;
  isBalanceAtBirth?: boolean;
}

export interface KundliAntardasha {
  lord: string;
  start: string;
  end: string;
  index?: number;
  of?: number;
}

export interface KundliDashaPeriod {
  lord: string;
  start: string;
  end: string;
  years?: number;
  index?: number;
  of?: number;
  level?: string;
}

export interface KundliDasha {
  birthNakshatra: string;
  birthNakshatraLord: string;
  progressAtBirth: number;
  balanceAtBirth: { lord: string; years: number; until: string };
  mahadashas: KundliMahadasha[];
  currentMahadasha: KundliMahadasha | null;
  antardashas: KundliAntardasha[];
  currentAntardasha: KundliAntardasha | null;
  currentPratyantardasha?: KundliDashaPeriod | null;
  currentSookshma?: KundliDashaPeriod | null;
  currentPrana?: KundliDashaPeriod | null;
  currentDashaFlow?: KundliDashaPeriod[];
}

export interface KundliNavtaraPosition {
  position: number;
  nakshatra: string;
  taraNumber: number;
  tara: string;
  specialRoles: string[];
  meaning: string;
}

export interface KundliNavtara {
  janmaNakshatra: string;
  positions: KundliNavtaraPosition[];
}

export interface KundliResponse {
  status: string;
  birth: KundliBirth;
  summary: KundliSummary;
  chart: KundliChart;
  planets: KundliPlanet[];
  panchang: KundliPanchang;
  dasha: KundliDasha;
  navtara: KundliNavtara;
  analysis?: AnalysisPayload | null;
  analysisStatus?: string;
}

export interface KundliTransit {
  planet: string;
  longitude: number;
  rashi: string;
  degree: number;
  nakshatra: string;
  pada: number;
  natalHouse: number;
}

export interface KundliTransitResponse {
  status: string;
  asOf: { timestamp: string; timezone: string };
  natalLagna: string;
  transits: KundliTransit[];
}

export interface KundliRequest {
  name?: string;
  date: string;
  time: string;
  place: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

const RASHI_ORDER = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

async function post<T>(path: string, payload: KundliRequest): Promise<T> {
  // Verified identity for the archive: present only when signed in.
  const identity = await authHeaders();
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...identity },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || (body as { status?: string }).status === 'error') {
    const message = (body as { message?: string }).message;
    throw new Error(message || `Kundli request failed (${response.status})`);
  }
  return body as T;
}

export function fetchKundli(payload: KundliRequest): Promise<KundliResponse> {
  return post<KundliResponse>('/kundli', payload);
}

export function fetchKundliTransits(payload: KundliRequest): Promise<KundliTransitResponse> {
  return postTransitWithRetry(payload);
}

export interface DashaChildrenResponse {
  status: string;
  level: string;
  parent: { lord: string; start: string; end: string };
  periods: KundliDashaPeriod[];
}

export async function fetchDashaChildren(
  level: number,
  parent: Pick<KundliDashaPeriod, 'lord' | 'start' | 'end'>,
): Promise<DashaChildrenResponse> {
  const identity = await authHeaders();
  const response = await fetch(`${API_BASE}/kundli/dasha/children`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...identity },
    body: JSON.stringify({ level, lord: parent.lord, start: parent.start, end: parent.end }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || (body as { status?: string }).status === 'error') {
    throw new Error('We could not load that Dasha level.');
  }
  return body as DashaChildrenResponse;
}

const TRANSIT_TIMEOUT_MS = 10000;

function transitError(message: string, status?: number): Error & { status?: number } {
  const error = new Error(message) as Error & { status?: number };
  error.status = status;
  return error;
}

async function postTransit(payload: KundliRequest): Promise<KundliTransitResponse> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), TRANSIT_TIMEOUT_MS);
  try {
    const identity = await authHeaders();
    const response = await fetch(`${API_BASE}/kundli/transits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...identity },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || (body as { status?: string }).status === 'error') {
      const status = response.status;
      const message = status >= 500 || status === 429
        ? 'Transit data could not be loaded.'
        : 'Please check the birth details and try again.';
      throw transitError(message, status);
    }
    return body as KundliTransitResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw transitError('Transit request timed out.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

async function postTransitWithRetry(payload: KundliRequest): Promise<KundliTransitResponse> {
  let attempt = 0;
  while (attempt < 2) {
    try {
      return await postTransit(payload);
    } catch (error) {
      const status = (error as { status?: number }).status;
      const retryable = !status || status === 429 || status >= 500;
      if (!retryable || attempt === 1) throw error;
      attempt += 1;
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    }
  }
  throw transitError('Transit data could not be loaded.');
}

/** Adapter so the existing D1 renderer can consume the Kundli chart response.
 *
 * KundliData requires: ascendantSign, ascendantDegree, houses AND
 * planetaryPositions (the renderer maps planetaryPositions by planet name to
 * read each planet's degree). All fields are populated from the API chart and
 * the object is returned structurally typed - no assertion.
 */
export function toKundliData(chart: KundliChart): KundliData {
  const planetsByHouse = new Map<number, string[]>();
  for (const planet of chart.planets) {
    const list = planetsByHouse.get(planet.house) ?? [];
    list.push(planet.planet);
    planetsByHouse.set(planet.house, list);
  }
  return {
    ascendantSign: chart.ascendant.rashi,
    ascendantDegree: `${chart.ascendant.degree.toFixed(2)}°`,
    houses: chart.houses.map((house) => ({
      houseNumber: house.number,
      sign: house.rashi,
      signNumber: RASHI_ORDER.indexOf(house.rashi) + 1,
      planets: planetsByHouse.get(house.number) ?? [],
    })),
    planetaryPositions: chart.planets.map((planet) => ({
      planet: planet.planet as KundliData['planetaryPositions'][number]['planet'],
      house: planet.house,
      sign: planet.rashi,
      degree: `${planet.degree.toFixed(2)}`,
      isRetrograde: planet.motion === 'Retrograde',
    })),
  };
}

export function birthDetailsFor(page: KundliResponse): BirthDetails {
  return {
    date: page.birth.date,
    time: page.birth.time,
    place: page.birth.place,
    latitude: page.birth.latitude,
    longitude: page.birth.longitude,
    timezone: page.birth.timezone,
  };
}

// ---------------------------------------------------------------- analysis
export type RelationshipQuality = 'FRIEND' | 'ENEMY' | 'NEUTRAL';

export interface BnnConnection {
  referencePlanet: string;
  referenceRashi: string;
  targetPlanet: string;
  targetRashi: string;
  relativePosition: number;
  connectionGroup: string | null;
  isPrimary: boolean;
  direction: string;
  layer: string;
  relationshipQuality: RelationshipQuality;
}

export interface NodeLayer {
  nodeRashi: string;
  dispositor: string | null;
  dispositorRashi: string | null;
  direct: BnnConnection[];
  operational: BnnConnection[];
  operationalReferenceRashi: string;
}

export interface BnnConnections {
  connections: Record<string, BnnConnection[]>;
  retrogradeLayers: Record<string, Record<string, BnnConnection[]>>;
  nodeLayers: Record<string, NodeLayer>;
  primaryPositions: number[];
  excludedPositions: number[];
  mechanismOnly: boolean;
  blocked: string;
}

export interface StrengthIsolation {
  isIsolated: boolean;
  isolationLevel: string;
  presentStructuralPositions: number[];
  presentTrinalPositions: number[];
  missingStructuralPositions: number[];
  missingTrinalPositions: number[];
  note: string;
}

export interface StrengthEvidence {
  referencePlanet: string;
  available: boolean;
  rashi?: string;
  house?: number;
  trinalConnections: string[];
  forwardConnections: string[];
  backwardConnections: string[];
  struggleConnections: string[];
  gainConnections: string[];
  oppositionConnections: string[];
  friendlyConnections: string[];
  enemyConnections: string[];
  neutralConnections: string[];
  hasForwardSupport: boolean;
  hasBackwardSupport: boolean;
  hasOpposition: boolean;
  hasThreeElevenNetwork: boolean;
  hasTrinalNetwork: boolean;
  isIsolated: boolean;
  isolation?: StrengthIsolation;
  dignity: string;
  combustion: { isCombust: boolean; note: string } | null;
  kartariCondition: string;
  kartariEvidence?: { behind12th: string | null; ahead2nd: string | null };
  supportReasons: string[];
  pressureReasons: string[];
  classification: null;
  classificationStatus: string;
  retrogradeLayers?: Record<string, BnnConnection[]>;
  nodeDispositorLayer?: {
    dispositor: string | null;
    dispositorRashi: string | null;
    operational: BnnConnection[];
    layer: string;
  };
}

export interface StrengthReport {
  planets: Record<string, StrengthEvidence>;
  classificationStatus: string;
  weights: null;
  note: string;
}

export interface MalaShreeChain {
  startingPlanet: string;
  chain: string[];
  chainArrow: string;
  uniquePlanets: string[];
  count: number;
  cycleStart: string | null;
  cycle: string[];
  cycleArrow: string;
  isCycle: boolean;
  terminated: boolean;
}

export interface StandardAspect {
  planet: string;
  fromHouse: number;
  aspects: number[];
  offsets: number[];
}

export interface MoonChartPayload {
  lagnaSign: string;
  placements: Record<string, { rashi: string; house: number; longitude?: number }>;
}

export interface AnalysisPayload {
  lagna: {
    lagnaSign: string;
    lagnaNumber: number;
    lagnesh: string;
    lagneshRashi?: string | null;
    lagneshHouse?: number | null;
  };
  atmakaraka: {
    atmakaraka: string | null;
    degreeInSign?: number;
    degrees: Record<string, number>;
    excluded: string[];
    ranking?: string[];
  };
  yogakaraka: string | null;
  maraka: { houses: number[]; signs: Record<string, string>; lords: Record<string, string>;
            primaryMarakaLords: string[]; note: string };
  badhaka: { modality: string | null; house: number | null; sign: string | null; lord: string | null };
  houseLords: Record<string, { sign: string; lord: string }>;
  dignity: Record<string, string[]>;
  conjunctions: Array<{ type: string; planets: string[]; rashi: string; separation?: number }>;
  bnnConnections: BnnConnections;
  standardAspects: StandardAspect[];
  strength: StrengthReport;
  dispositorChains: Record<string, MalaShreeChain>;
  malaShree: MalaShreeChain[];
  modalities: Record<string, string[]>;
  elements: Record<string, string[]>;
  purushartha: Record<string, string[]>;
  moonChart: MoonChartPayload;
  bhavaChalit: null;
  bhavaChalitStatus: string;
}
