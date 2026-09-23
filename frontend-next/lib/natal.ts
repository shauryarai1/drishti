import { fetchKundli } from './kundli';
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
  if (profile.latitude == null || profile.longitude == null) {
    // Never fabricate coordinates: a profile without a resolved birth place
    // cannot be charted.
    throw new Error('This profile has no saved birth coordinates.');
  }
  // The EXISTING authoritative Kundli engine - the same `build_kundli` path the
  // /kundli page and the compatibility report use. The /interpretation endpoint
  // deliberately hides planets and nakshatras, so it can never be used here.
  const chart = await fetchKundli({
    name: profile.name,
    date: profile.birth_date,
    time: profile.birth_time,
    place: profile.birth_place_name,
    latitude: profile.latitude,
    longitude: profile.longitude,
    timezone: profile.timezone || 'Asia/Kolkata',
  });
  const moon = (chart.planets ?? []).find((row) => row.planet === 'Moon');
  const moonRashi = moon?.rashi ?? '';
  const janmaNakshatra = moon?.nakshatra ?? '';
  if (!moonRashi || !janmaNakshatra) {
    throw new Error('The natal Moon position could not be established for this profile.');
  }
  return { moonRashi, janmaNakshatra };
}
