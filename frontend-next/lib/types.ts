/**
 * DRISHTI Type System
 * Clear contracts between data layers, calculation endpoints, and presentation components.
 */

export interface BirthDetails {
  date: string; // YYYY-MM-DD
  time: string; // HH:mm
  place: string; // City, Region, Country
  latitude?: number;
  longitude?: number;
  timezone?: string;
}

export interface PlanetPosition {
  planet: 'Sun' | 'Moon' | 'Mars' | 'Mercury' | 'Jupiter' | 'Venus' | 'Saturn' | 'Rahu' | 'Ketu' | 'Uranus' | 'Neptune' | 'Pluto' | 'Ascendant';
  symbol?: string;
  house: number; // 1 to 12
  sign: string; // Aries, Taurus, etc.
  degree?: string;
  isRetrograde?: boolean;
}

export interface KundliHouse {
  houseNumber: number;
  sign: string;
  signNumber: number; // 1 (Aries) - 12 (Pisces)
  planets: string[]; // e.g. ['Ve', 'Me']
}

export interface NorthPlanetPosition {
  key: string;
  name: string;
  englishName: string;
  symbol: string;
  degreeInSign: number;
  isRetrograde: boolean;
  isCombust: boolean;
  dignity: string;
  house: number;
}

export interface NorthHouseData {
  houseNumber: number;
  signNumber: number;
  signEnglish: string;
  planets: NorthPlanetPosition[];
}

export interface KundliData {
  ascendantSign: string;
  ascendantDegree?: string;
  houses: KundliHouse[];
  planetaryPositions: PlanetPosition[];
}

export interface InsightArea {
  id: 'attention' | 'protect' | 'danger';
  stepNumber: string;
  label: string;
  title: string;
  subtitle: string;
  quote: string;
  summary: string;
  body: string[];
  watchFor: {
    primary: string;
    points: string[];
  };
  environmentalTheme: 'light' | 'mixed' | 'deep-crimson';
}

export interface CautionPeriod {
  id: string;
  period: string; // e.g. "Oct 14 — Nov 28, 2026"
  intensity: 'heightened' | 'moderate' | 'critical';
  title: string;
  description: string;
  focus: string;
  isCurrent?: boolean;
}

export interface DrishtiReading {
  id: string;
  createdAt: string;
  birthDetails: BirthDetails;
  ascendant: string;
  headline: string;
  overview: string;
  kundli: KundliData;
  attentionArea: InsightArea;
  protectArea: InsightArea;
  dangerArea: InsightArea;
  cautionPeriods: CautionPeriod[];
  takeaway: {
    title: string;
    thesis: string;
    guidance: string;
    anchorWords: string[];
  };
}

export interface PlaceSuggestion {
  id: string;
  name: string;
  region: string;
  country: string;
  coordinates: {
    lat: number;
    lng: number;
  };
}
