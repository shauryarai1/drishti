import { api } from './api';
import type { BirthDetails } from './types';
import type { BirthProfile } from './profiles';

/**
 * Natal values for a birth profile, derived from the EXISTING authoritative
 * KAVACH chart calculation (the same path /reading uses). Nothing is stored:
 * Moon Rashi and Janma Nakshatra are recalculated from birth facts, so they can
 * never go stale and the user is never asked for them.
 */

export interface NatalValues {
  moonRashi: string;
  janmaNakshatra: string;
}

export function birthDetailsForProfile(profile: BirthProfile): BirthDetails {
  return {
    name: profile.name,
    date: profile.birth_date,
    time: profile.birth_time,
    place: profile.birth_place_name,
    latitude: profile.latitude ?? undefined,
    longitude: profile.longitude ?? undefined,
    timezone: profile.timezone || undefined,
  };
}

export async function deriveNatal(profile: BirthProfile): Promise<NatalValues> {
  const reading = await api.getInterpretation(birthDetailsForProfile(profile));
  const chart = (reading as { chart?: { planets?: Array<{ planet?: string; name?: string; rashi?: string; nakshatra?: string }> } }).chart;
  const moon = (chart?.planets ?? []).find(
    (row) => (row.planet ?? row.name) === 'Moon',
  );
  const moonRashi = moon?.rashi ?? '';
  const janmaNakshatra = moon?.nakshatra ?? '';
  if (!moonRashi || !janmaNakshatra) {
    throw new Error('The natal Moon position could not be established for this profile.');
  }
  return { moonRashi, janmaNakshatra };
}
