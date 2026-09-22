/**
 * Verified session token for the FastAPI backend.
 *
 * A page being signed in does NOT tell FastAPI who the user is: the request has
 * to carry the Supabase access token so the backend can verify it and associate
 * the archived submission with the authenticated account.
 *
 * The token is read from the existing Supabase session and used only as an
 * Authorization header. It is never logged, never placed in a URL, never stored
 * in the archive and never rendered.
 */

import { getSupabase } from './supabase';

/** `{ Authorization: "Bearer …" }` when a session exists, otherwise `{}`. */
export async function authHeaders(): Promise<Record<string, string>> {
  const supabase = getSupabase();
  if (!supabase) return {};
  try {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    // An unavailable session must never break a product request.
    return {};
  }
}
