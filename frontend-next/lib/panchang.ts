/**
 * Panchang types + adapter to the existing KAVACH Kundli renderer.
 *
 * Panchang data is a separate calculation layer; nothing here touches the
 * KAVACH interpretation theory.
 */

export interface PanchangElement {
  index: number;
  name: string;
  next_name: string;
  start: string | null;
  end: string | null;
  start_local: string | null;
  end_local: string | null;
  paksha?: string;
  number_in_paksha?: number;
  pada?: number;
  pada_end?: string | null;
  pada_end_local?: string | null;
  lord?: string;
}

export interface PanchangPeriod {
  name: string;
  kind: string;
  start: string;
  end: string;
  local_start: string;
  local_end: string;
  note?: string;
  active: boolean;
}

export interface PanchangHora {
  planet: string;
  nature: string;
  part: 'day' | 'night';
  sequence_number: number;
  start: string;
  end: string;
  start_local: string;
  end_local: string;
  is_current: boolean;
}

export interface PanchangResult {
  day: { date: string; weekday: string; vara: string; weekday_index: number };
  location: { label: string; latitude: number; longitude: number };
  request: { date: string; timezone: string; reference: string };
  sun_moon: Record<string, number | string | null>;
  panchanga: {
    tithi: PanchangElement;
    nakshatra: PanchangElement;
    yoga: PanchangElement;
    karana: { current: string | null; sequence: Array<Record<string, unknown>> };
    vara: { index: number; name: string; english: string };
  };
  sun_moon_rashi: {
    moon: { name: string; english: string; start: string | null; end: string | null };
    sun: { name: string; english: string; sankranti: string | null };
  };
  d1: {
    instant: string;
    lagna: { sign: string; degree_in_sign: number; nakshatra: string; pada: number };
    positions: Array<{
      planet: string;
      sign: string;
      degree_in_sign: number;
      nakshatra: string;
      pada: number;
      house: number;
      retrograde: boolean;
      sign_index: number;
    }>;
    houses: Array<{ house: number; sign: string; sign_index: number; planets: string[] }>;
  };
  hora: {
    weekday_lord: string;
    day_hora_minutes: number;
    night_hora_minutes: number;
    day: PanchangHora[];
    night: PanchangHora[];
    current: PanchangHora | null;
    next: PanchangHora | null;
  };
  balam: {
    tarabalam: Array<{ nakshatra: string; tara: string; good: boolean }>;
    chandrabalam: Array<{ rashi: string; house_from_janma: number; good: boolean }>;
    good_tarabalam: string[];
    good_chandrabalam: string[];
  };
  auspicious: PanchangPeriod[];
  inauspicious: PanchangPeriod[];
  choghadiya: {
    day: Array<{ name: string; classification: string; local_start: string; local_end: string }>;
    night: Array<{ name: string; classification: string; local_start: string; local_end: string }>;
  };
  calendar: Record<string, string | number | null>;
  notes: string[];
}

/**
 * Adapt the Panchang sunrise D1 into the shape the existing KAVACH Kundli
 * renderer already consumes. House 1 is the actual sunrise Ascendant.
 */
export function d1ToKundliData(d1: PanchangResult['d1']) {
  return {
    ascendantSign: d1.lagna.sign,
    ascendantDegree: `${d1.lagna.degree_in_sign.toFixed(2)}°`,
    houses: d1.houses.map((house) => ({
      houseNumber: house.house,
      sign: house.sign,
      signNumber: house.sign_index + 1,
      planets: house.planets,
    })),
    planetaryPositions: d1.positions.map((p) => ({
      planet: p.planet as never,
      house: p.house,
      sign: p.sign,
      degree: `${p.degree_in_sign.toFixed(2)}°`,
    })),
  };
}
