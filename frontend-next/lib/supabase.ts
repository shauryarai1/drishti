import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Browser Supabase client.
 *
 * Only the public anon key is ever read here, and only through NEXT_PUBLIC_*
 * variables. The service-role key must never reach the frontend or the repo.
 * Sessions are held by the provider's own supported browser mechanism
 * (supabase-js own storage + auto refresh); no custom auth tokens are invented.
 */

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;

// Supabase now issues a browser-safe publishable key ("sb_publishable_...") which
// is the same credential role as the legacy anon JWT, just under a newer name.
// Accept either variable name so a project configured either way resolves.
const anonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const isSupabaseConfigured = Boolean(url && anonKey);

export const HISTORY_TABLE = 'saved_readings';

let client: SupabaseClient | null = null;

/** Returns the shared client, or null when the environment is not configured. */
export function getSupabase(): SupabaseClient | null {
  if (!url || !anonKey) return null;
  if (!client) {
    client = createClient(url, anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        // Lets the password-recovery link restore the session on the reset route.
        detectSessionInUrl: true,
      },
    });
  }
  return client;
}
