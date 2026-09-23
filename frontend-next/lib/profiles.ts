import { getSupabase } from './supabase';

/**
 * Birth profiles: the account owner's PRIMARY profile plus any number of
 * OTHER PERSON profiles (family, partner, client).
 *
 * Ownership comes from the authenticated session, and the database enforces it
 * again with row level security, so a tampered id can never reach another
 * account's rows. No derived astrology is stored: natal positions are
 * recalculated from the authoritative engine, so they cannot go stale. Nothing
 * here is written to browser storage.
 */

export const PROFILES_TABLE = 'birth_profiles';

export interface BirthProfile {
  id: string;
  user_id: string;
  name: string;
  birth_date: string;
  birth_time: string;
  birth_place_name: string;
  latitude: number | null;
  longitude: number | null;
  timezone: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface BirthProfileInput {
  name: string;
  birth_date: string;
  birth_time: string;
  birth_place_name: string;
  latitude?: number | null;
  longitude?: number | null;
  timezone?: string;
}

const UNAVAILABLE = 'Accounts are not available on this deployment yet.';
const LOAD_ERROR = 'We could not load your birth profiles. Please try again.';
const SAVE_ERROR = 'We could not save this profile. Please try again.';
const UPDATE_ERROR = 'We could not update that profile. Please try again.';
const DELETE_ERROR = 'We could not delete that profile. Please try again.';

const COLUMNS =
  'id, user_id, name, birth_date, birth_time, birth_place_name, latitude, longitude, timezone, is_primary, created_at, updated_at';

function client() {
  const supabase = getSupabase();
  if (!supabase) throw new Error(UNAVAILABLE);
  return supabase;
}

function clean(input: BirthProfileInput) {
  return {
    name: (input.name ?? '').trim(),
    birth_date: (input.birth_date ?? '').trim(),
    birth_time: (input.birth_time ?? '').trim(),
    birth_place_name: (input.birth_place_name ?? '').trim(),
    latitude: input.latitude ?? null,
    longitude: input.longitude ?? null,
    timezone: (input.timezone ?? '').trim() || 'Asia/Kolkata',
  };
}

export async function listProfiles(userId: string): Promise<BirthProfile[]> {
  const { data, error } = await client()
    .from(PROFILES_TABLE)
    .select(COLUMNS)
    .eq('user_id', userId)
    .order('is_primary', { ascending: false })
    .order('created_at', { ascending: true });
  if (error) throw new Error(LOAD_ERROR);
  return (data ?? []) as unknown as BirthProfile[];
}

/** The account's primary profile, or null when setup has not happened yet. */
export async function getPrimaryProfile(userId: string): Promise<BirthProfile | null> {
  const { data, error } = await client()
    .from(PROFILES_TABLE)
    .select(COLUMNS)
    .eq('user_id', userId)
    .eq('is_primary', true)
    .maybeSingle();
  if (error) throw new Error(LOAD_ERROR);
  return (data as unknown as BirthProfile) ?? null;
}

/** Create the primary profile (one-time setup). */
export async function createPrimaryProfile(
  userId: string,
  input: BirthProfileInput,
): Promise<BirthProfile> {
  const { data, error } = await client()
    .from(PROFILES_TABLE)
    .insert({ ...clean(input), user_id: userId, is_primary: true })
    .select(COLUMNS)
    .single();
  if (error || !data) throw new Error(SAVE_ERROR);
  return data as unknown as BirthProfile;
}

/** Add another person. Never touches the primary profile. */
export async function createOtherPerson(
  userId: string,
  input: BirthProfileInput,
): Promise<BirthProfile> {
  const { data, error } = await client()
    .from(PROFILES_TABLE)
    .insert({ ...clean(input), user_id: userId, is_primary: false })
    .select(COLUMNS)
    .single();
  if (error || !data) throw new Error(SAVE_ERROR);
  return data as unknown as BirthProfile;
}

/** Edit any profile. `is_primary` is never changed here. */
export async function updateProfile(
  userId: string,
  id: string,
  input: BirthProfileInput,
): Promise<BirthProfile> {
  const { data, error } = await client()
    .from(PROFILES_TABLE)
    .update(clean(input))
    .eq('user_id', userId)
    .eq('id', id)
    .select(COLUMNS)
    .single();
  if (error || !data) throw new Error(UPDATE_ERROR);
  return data as unknown as BirthProfile;
}

/**
 * Promote a profile to primary, demoting the current one first. The partial
 * unique index means the demotion must land before the promotion.
 */
export async function makePrimary(userId: string, id: string): Promise<void> {
  const supabase = client();
  const { error: demoteError } = await supabase
    .from(PROFILES_TABLE)
    .update({ is_primary: false })
    .eq('user_id', userId)
    .eq('is_primary', true)
    .neq('id', id);
  if (demoteError) throw new Error(UPDATE_ERROR);

  const { error: promoteError } = await supabase
    .from(PROFILES_TABLE)
    .update({ is_primary: true })
    .eq('user_id', userId)
    .eq('id', id);
  if (promoteError) throw new Error(UPDATE_ERROR);
}

/** Delete an other-person profile. The primary profile is never deletable here. */
export async function deleteOtherPerson(userId: string, id: string): Promise<void> {
  const { error } = await client()
    .from(PROFILES_TABLE)
    .delete()
    .eq('user_id', userId)
    .eq('id', id)
    .eq('is_primary', false);
  if (error) throw new Error(DELETE_ERROR);
}
