import { getSupabase, HISTORY_TABLE } from './supabase';
import type { KundliResponse } from './kundli';

/**
 * Private reading history.
 *
 * Every operation is scoped to the authenticated user id, and the database
 * additionally enforces ownership with row level security, so a tampered id or
 * user_id can never reach another account's rows.
 */

export type ReadingType = 'kundli' | 'daily' | 'weekly' | 'life_summary' | 'dasha' | 'ask' | 'compatibility';

export const SCHEMA_VERSION = 1;

export const READING_TYPE_LABELS: Record<ReadingType, string> = {
  kundli: 'Kundli',
  daily: 'Daily Prediction',
  weekly: 'Your Week',
  life_summary: 'Life Summary',
  dasha: 'Dasha Reading',
  ask: 'Ask KAVACH',
  compatibility: 'Matchmaking',
};

/** Metadata only: the heavy result payload is fetched on open. */
export interface SavedReadingSummary {
  id: string;
  user_id: string;
  type: ReadingType;
  title: string;
  input_data: Record<string, unknown>;
  schema_version: number;
  created_at: string;
  updated_at: string;
}

export interface SavedReading extends SavedReadingSummary {
  result_data: unknown;
}

export interface KundliHistoryInput {
  name: string;
  date: string;
  time: string;
  place: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

const UNAVAILABLE = 'Accounts are not available on this deployment yet.';
const LOAD_ERROR = 'We could not load your history. Please try again.';
const SAVE_ERROR = 'We could not save this reading. Please try again.';
const UPDATE_ERROR = 'We could not update that reading. Please try again.';
const DELETE_ERROR = 'We could not delete that reading. Please try again.';

function client() {
  const supabase = getSupabase();
  if (!supabase) throw new Error(UNAVAILABLE);
  return supabase;
}

const SUMMARY_COLUMNS = 'id, user_id, type, title, input_data, schema_version, created_at, updated_at';

export function buildKundliTitle(name: string | null | undefined, date: string): string {
  const native = (name ?? '').trim();
  if (native) return `${native}'s Kundli`;
  return `Kundli · ${date}`;
}

export async function listReadings(userId: string, type?: ReadingType): Promise<SavedReadingSummary[]> {
  let query = client()
    .from(HISTORY_TABLE)
    .select(SUMMARY_COLUMNS)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (type) query = query.eq('type', type);

  const { data, error } = await query;
  if (error) throw new Error(LOAD_ERROR);
  return (data ?? []) as unknown as SavedReadingSummary[];
}

export async function getReading(userId: string, id: string): Promise<SavedReading | null> {
  const { data, error } = await client()
    .from(HISTORY_TABLE)
    .select(`${SUMMARY_COLUMNS}, result_data`)
    .eq('user_id', userId)
    .eq('id', id)
    .maybeSingle();

  if (error) throw new Error(LOAD_ERROR);
  return (data as unknown as SavedReading) ?? null;
}

export async function saveReading(
  userId: string,
  input: { type: ReadingType; title: string; input_data: Record<string, unknown>; result_data: unknown },
): Promise<string> {
  const { data, error } = await client()
    .from(HISTORY_TABLE)
    .insert({
      user_id: userId,
      type: input.type,
      title: input.title,
      input_data: input.input_data,
      result_data: input.result_data ?? null,
      schema_version: SCHEMA_VERSION,
    })
    .select('id')
    .single();

  if (error || !data) throw new Error(SAVE_ERROR);
  return (data as { id: string }).id;
}

export async function saveKundliReading(
  userId: string,
  input: KundliHistoryInput,
  result: KundliResponse,
): Promise<string> {
  return saveReading(userId, {
    type: 'kundli',
    title: buildKundliTitle(input.name, input.date),
    input_data: { ...input },
    result_data: result,
  });
}

/** Compatibility history input: both chart people, kept separate. */
export interface CompatibilityHistoryInput {
  bride_name: string;
  bride_date: string;
  bride_time: string;
  bride_place: string;
  bride_latitude?: number;
  bride_longitude?: number;
  bride_timezone?: string;
  groom_name: string;
  groom_date: string;
  groom_time: string;
  groom_place: string;
  groom_latitude?: number;
  groom_longitude?: number;
  groom_timezone?: string;
}

export function buildCompatibilityTitle(bride: string, groom: string): string {
  const a = (bride ?? '').trim() || 'Person 1';
  const b = (groom ?? '').trim() || 'Person 2';
  return `${a} & ${b} — Matchmaking`;
}

export async function saveCompatibilityReading(
  userId: string,
  input: CompatibilityHistoryInput,
  result: unknown,
): Promise<string> {
  return saveReading(userId, {
    type: 'compatibility',
    title: buildCompatibilityTitle(input.bride_name, input.groom_name),
    input_data: { ...input },
    result_data: result,
  });
}

export async function renameReading(userId: string, id: string, title: string): Promise<void> {  const clean = title.trim();
  if (!clean) throw new Error('Please enter a title.');

  const { error } = await client()
    .from(HISTORY_TABLE)
    .update({ title: clean })
    .eq('user_id', userId)
    .eq('id', id);

  if (error) throw new Error(UPDATE_ERROR);
}

export async function deleteReading(userId: string, id: string): Promise<void> {
  const { error } = await client()
    .from(HISTORY_TABLE)
    .delete()
    .eq('user_id', userId)
    .eq('id', id);

  if (error) throw new Error(DELETE_ERROR);
}
