import { BirthDetails, DrishtiReading, KundliData, PlaceSuggestion } from './types';

const API_ORIGIN =
  process.env.NODE_ENV === 'production'
    ? 'https://drishti-5j3u.onrender.com'
    : 'http://localhost:8000';

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) throw new Error((await response.text().catch(() => '')) || `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

function adaptKundli(chart: RawChart): KundliData {
  const planets = [...(chart.planets || []), ...(chart.extra_planets || [])];
  return {
    ascendantSign: chart.ascendant?.sign || chart.ascendant_sign || '—',
    ascendantDegree: chart.ascendant?.degree === undefined ? undefined : `${chart.ascendant.degree.toFixed(2)}°`,
    houses: Array.from({ length: 12 }, (_, index) => {
      const houseNumber = index + 1;
      const house = chart.houses?.find((item) => item.number === houseNumber);
      return { houseNumber, sign: house?.sign || '—', signNumber: Math.max(1, signNames.indexOf(house?.sign || '') + 1), planets: planets.filter((planet) => planet.house === houseNumber).map((planet) => planet.name) };
    }),
    planetaryPositions: planets.map((planet) => ({ planet: planet.name as never, house: planet.house, sign: planet.sign, degree: planet.degree === undefined ? undefined : `${planet.degree.toFixed(2)}°` })),
  };
}

function adaptArea(raw: RawArea, id: 'attention' | 'protect' | 'danger', stepNumber: string, environmentalTheme: 'light' | 'mixed' | 'deep-crimson') {
  return {
    id, stepNumber,
    label: id === 'attention' ? 'ATTENTION AREA' : id === 'protect' ? 'PROTECT THIS AREA' : 'DANGER AREA',
    title: raw.area,
    subtitle: id === 'attention' ? 'Where natural instinct needs conscious calibration' : id === 'protect' ? 'Know where to stop' : 'What should not be ignored',
    quote: raw.hook || raw.takeaway || raw.description,
    summary: raw.description,
    body: raw.potential_impact ? [raw.description, raw.potential_impact] : [raw.description],
    watchFor: { primary: raw.mindful_of?.[0] || 'Repeatedly ignoring the warning signs in this area.', points: raw.mindful_of?.slice(1) || [] },
    environmentalTheme,
  };
}

export const api = {
  async searchPlaces(query: string): Promise<PlaceSuggestion[]> {
    if (!query.trim()) return [];
    const response = await request<{ results: Array<{ display: string; lat: number; lon: number }> }>(`/places/search?q=${encodeURIComponent(query.trim())}`);
    return (response.results || []).map((place, index) => {
      const parts = place.display.split(',').map((part) => part.trim());
      return { id: `${place.lat}-${place.lon}-${index}`, name: parts[0] || place.display, region: parts[1] || '', country: parts.slice(2).join(', ') || '', coordinates: { lat: place.lat, lng: place.lon } };
    });
  },

  async calculateChart(birthDetails: BirthDetails) {
    const raw = await request<RawChart>('/chart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    if (raw.status === 'ERROR') throw new Error(raw.reason || 'Chart calculation failed.');
    return { kundli: adaptKundli(raw), ascendant: raw.ascendant?.sign || raw.ascendant_sign || '—' };
  },

  async getInterpretation(birthDetails: BirthDetails): Promise<DrishtiReading> {
    const raw = await request<RawInterpretation>('/interpretation', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    if (raw.status === 'error') throw new Error(raw.message || 'Unable to complete your reading.');
    const chart = raw.chart || await request<RawChart>('/chart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(birthDetails) });
    return {
      id: `reading-${Date.now()}`, createdAt: new Date().toISOString(), birthDetails,
      ascendant: chart.ascendant?.sign || chart.ascendant_sign || '—',
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
    period: `${item.start_date} — ${item.end_date}`,
    intensity: item.level === 'high' ? 'critical' as const : 'heightened' as const,
    title: item.title,
    description: item.guidance,
    focus: item.area,
  };
}
