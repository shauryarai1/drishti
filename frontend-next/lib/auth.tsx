'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { getSupabase, isSupabaseConfigured } from './supabase';

/**
 * Single shared session layer for the whole app.
 *
 * Every component reads auth state from this context so pages never query the
 * provider independently, and a guest browsing experience is preserved: when
 * Supabase is not configured the app simply resolves to "signed out".
 */

export type AuthStatus = 'loading' | 'signedOut' | 'signedIn';

export interface AuthActionResult {
  ok: boolean;
  /** Restrained, user-facing message. Never a raw provider or stack error. */
  message?: string;
}

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  session: Session | null;
  configured: boolean;
  signIn: (email: string, password: string) => Promise<AuthActionResult>;
  signUp: (email: string, password: string) => Promise<AuthActionResult>;
  signOut: () => Promise<void>;
  sendPasswordReset: (email: string, redirectTo: string) => Promise<AuthActionResult>;
  updatePassword: (password: string) => Promise<AuthActionResult>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const GENERIC_ERROR = 'We could not complete that request. Please try again.';

function describeAuthError(error: { message?: string; code?: string; status?: number } | null): string {
  if (!error) return GENERIC_ERROR;
  const code = (error.code ?? '').toLowerCase();
  const message = (error.message ?? '').toLowerCase();

  if (code === 'invalid_credentials' || message.includes('invalid login credentials')) {
    return 'That email and password combination did not match our records.';
  }
  if (code === 'email_not_confirmed' || message.includes('email not confirmed')) {
    return 'Please confirm your email address before signing in.';
  }
  if (code === 'user_already_exists' || message.includes('already registered')) {
    return 'An account with this email already exists. Try signing in instead.';
  }
  if (code === 'weak_password' || message.includes('password should be')) {
    return 'Please choose a stronger password of at least 8 characters.';
  }
  if (code === 'over_email_send_rate_limit' || message.includes('rate limit')) {
    return 'Too many attempts just now. Please wait a moment and try again.';
  }
  if (message.includes('unable to validate email') || message.includes('invalid format')) {
    return 'Please enter a valid email address.';
  }
  if (message.includes('failed to fetch') || message.includes('network')) {
    return 'We could not reach the server. Check your connection and try again.';
  }
  if (message.includes('session') && message.includes('expired')) {
    return 'Your session expired. Please sign in again.';
  }
  return GENERIC_ERROR;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) {
      setStatus('signedOut');
      return;
    }

    let active = true;

    // Local session first so the navbar resolves without a network round trip.
    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!active) return;
        setSession(data.session ?? null);
        setUser(data.session?.user ?? null);
        setStatus(data.session ? 'signedIn' : 'signedOut');
      })
      .catch(() => {
        if (!active) return;
        setStatus('signedOut');
      });

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) return;
      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      setStatus(nextSession ? 'signedIn' : 'signedOut');
    });

    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string): Promise<AuthActionResult> => {
    const supabase = getSupabase();
    if (!supabase) return { ok: false, message: 'Accounts are not available on this deployment yet.' };
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (error) return { ok: false, message: describeAuthError(error) };
    return { ok: true };
  }, []);

  const signUp = useCallback(async (email: string, password: string): Promise<AuthActionResult> => {
    const supabase = getSupabase();
    if (!supabase) return { ok: false, message: 'Accounts are not available on this deployment yet.' };
    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: { emailRedirectTo: `${window.location.origin}/account` },
    });
    if (error) return { ok: false, message: describeAuthError(error) };
    if (!data.session) {
      return { ok: true, message: 'Check your email to confirm your account, then sign in.' };
    }
    return { ok: true };
  }, []);

  const signOut = useCallback(async () => {
    const supabase = getSupabase();
    if (!supabase) return;
    await supabase.auth.signOut();
  }, []);

  const sendPasswordReset = useCallback(
    async (email: string, redirectTo: string): Promise<AuthActionResult> => {
      const supabase = getSupabase();
      if (!supabase) return { ok: false, message: 'Accounts are not available on this deployment yet.' };
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), { redirectTo });
      if (error) return { ok: false, message: describeAuthError(error) };
      return { ok: true, message: 'If that email is registered, a reset link is on its way.' };
    },
    [],
  );

  const updatePassword = useCallback(async (password: string): Promise<AuthActionResult> => {
    const supabase = getSupabase();
    if (!supabase) return { ok: false, message: 'Accounts are not available on this deployment yet.' };
    const { error } = await supabase.auth.updateUser({ password });
    if (error) return { ok: false, message: describeAuthError(error) };
    return { ok: true, message: 'Your password has been updated.' };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      session,
      configured: isSupabaseConfigured,
      signIn,
      signUp,
      signOut,
      sendPasswordReset,
      updatePassword,
    }),
    [status, user, session, signIn, signUp, signOut, sendPasswordReset, updatePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
