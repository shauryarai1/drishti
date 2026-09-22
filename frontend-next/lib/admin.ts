'use client';

import { API_BASE } from './api';
import { getSupabase } from './supabase';

/** Owner dashboard client. Every call carries the verified Supabase access token. */

export interface AdminSubmissionRow {
  id: string;
  created_at: string;
  completed_at?: string | null;
  user_id: string | null;
  visitor_session_id?: string | null;
  product: string;
  status: string;
  input_data: Record<string, unknown>;
  schema_version?: number;
  account_email?: string | null;
  /** Safe display name from verified Supabase metadata, when one exists. */
  account_name?: string | null;
  /** The chart person's name (Kundli Person Name), separate from the account. */
  person_name?: string | null;
}

export interface AdminSubmissionDetail extends AdminSubmissionRow {
  result_data: unknown;
  error_category?: string | null;
}

export interface AdminStats {
  total: number;
  today: number;
  guests: number;
  accounts: number;
  [product: string]: number;
}

export interface AdminFilters {
  product: string;
  visitor: string;
  range: string;
  q: string;
  page: number;
  pageSize: number;
}

export const PRODUCT_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'reading', label: 'KAVACH Reading' },
  { value: 'kundli', label: 'Kundli' },
  { value: 'daily', label: 'Daily Prediction' },
  { value: 'weekly', label: 'Your Week' },
  { value: 'life_summary', label: 'Life Summary' },
  { value: 'dasha', label: 'Dasha Reading' },
  { value: 'ask', label: 'Ask KAVACH' },
  { value: 'panchang', label: 'Panchang' },
] as const;

export const PRODUCT_LABELS: Record<string, string> = {
  kundli: 'KUNDLI',
  reading: 'KAVACH READING',
  daily: 'DAILY PREDICTION',
  weekly: 'YOUR WEEK',
  life_summary: 'LIFE SUMMARY',
  ask: 'ASK KAVACH',
  dasha: 'DASHA READING',
  panchang: 'PANCHANG',
};

export const VISITOR_FILTERS = [
  { value: 'all', label: 'All visitors' },
  { value: 'guests', label: 'Guests' },
  { value: 'accounts', label: 'Accounts' },
] as const;

export const RANGE_FILTERS = [
  { value: 'all', label: 'All time' },
  { value: 'today', label: 'Today' },
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
] as const;

const NO_SESSION = 'Sign in with an administrator account to continue.';
const LOAD_ERROR = 'We could not load the archive. Please try again.';
const DETAIL_ERROR = 'Could not load submission details.';
const NOT_FOUND = 'That submission could not be found.';

async function adminFetch<T>(path: string, init?: RequestInit, fallbackMessage = LOAD_ERROR): Promise<T> {
  const supabase = getSupabase();
  if (!supabase) throw new Error('Administration is not available on this deployment yet.');
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error(NO_SESSION);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { ...(init?.headers ?? {}), Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error(fallbackMessage);
  }

  if (response.status === 401) throw new Error('Your session expired. Please sign in again.');
  if (response.status === 403) throw new Error('This account is not authorised for administration.');
  if (response.status === 503) throw new Error('Administration is not configured on this deployment yet.');
  if (response.status === 404) throw new Error(NOT_FOUND);
  if (!response.ok) throw new Error(fallbackMessage);

  return (await response.json()) as T;
}

export async function fetchAdminStats(): Promise<AdminStats> {
  const body = await adminFetch<{ stats: AdminStats }>('/admin/stats');
  return body.stats;
}

export async function fetchAdminSubmissions(filters: AdminFilters): Promise<{
  total: number;
  submissions: AdminSubmissionRow[];
}> {
  const params = new URLSearchParams({
    product: filters.product,
    visitor: filters.visitor,
    range: filters.range,
    q: filters.q,
    page: String(filters.page),
    page_size: String(filters.pageSize),
  });
  const body = await adminFetch<{ total: number; submissions: AdminSubmissionRow[] }>(
    `/admin/submissions?${params.toString()}`,
  );
  return { total: body.total ?? 0, submissions: body.submissions ?? [] };
}

export async function fetchAdminSubmission(id: string): Promise<AdminSubmissionDetail> {
  const body = await adminFetch<{ submission: AdminSubmissionDetail }>(
    `/admin/submissions/${encodeURIComponent(id)}`,
    undefined,
    DETAIL_ERROR,
  );
  return body.submission;
}

export async function deleteAdminSubmission(id: string): Promise<void> {
  await adminFetch<{ status: string }>(`/admin/submissions/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
