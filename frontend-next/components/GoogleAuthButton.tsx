'use client';

import React, { useState } from 'react';
import { useAuth } from '../lib/auth';

/**
 * Google sign-in through the existing Supabase Auth layer.
 *
 * No second auth system, no extra library: this calls
 * supabase.auth.signInWithOAuth({ provider: 'google' }) from lib/auth and
 * returns the user to the validated internal path they came from.
 */

interface GoogleAuthButtonProps {
  /** Internal KAVACH path to return to (validated by safeNextPath). */
  nextPath: string;
  className?: string;
}

export function GoogleAuthButton({ nextPath, className = '' }: GoogleAuthButtonProps) {
  const { signInWithGoogle, configured } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const start = async () => {
    if (busy) return;
    setBusy(true);
    setError('');
    const result = await signInWithGoogle(nextPath);
    if (!result.ok) {
      setBusy(false);
      setError(result.message ?? 'We could not start Google sign-in. Please try again.');
      return;
    }
    // On success the browser leaves for Google; the button stays disabled.
  };

  return (
    <div className={className}>
      <button
        type="button"
        onClick={() => void start()}
        disabled={busy || !configured}
        className="inline-flex h-11 w-full items-center justify-center gap-3 rounded border border-[#EEE9DF]/25 bg-[#F7F5F0] px-5 font-mono text-[11px] uppercase tracking-[0.18em] text-[#160A0C] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <GoogleMark />
        {busy ? 'Opening Google…' : 'CONTINUE WITH GOOGLE'}
      </button>
      {error && (
        <p role="alert" className="mt-2 text-center text-[12px] text-[#EEE9DF]/70">
          {error}
        </p>
      )}
    </div>
  );
}

/** Restrained inline mark: no external image request, no dependency. */
function GoogleMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4">
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.51h6.47a5.53 5.53 0 0 1-2.4 3.63v3h3.86c2.26-2.09 3.56-5.17 3.56-8.87z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09A11.99 11.99 0 0 0 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.27 14.28a7.2 7.2 0 0 1 0-4.56V6.63H1.29a12 12 0 0 0 0 10.74l3.98-3.09z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.7 0 3.99 2.47 1.29 6.63l3.98 3.09C6.22 6.86 8.87 4.75 12 4.75z"
      />
    </svg>
  );
}

/** The "──────── OR ────────" rule between Google and email/password. */
export function AuthOrDivider() {
  return (
    <div className="my-5 flex items-center gap-3">
      <span className="h-[1px] flex-1 bg-[#A62A34]/25" />
      <span className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#EEE9DF]/45">or</span>
      <span className="h-[1px] flex-1 bg-[#A62A34]/25" />
    </div>
  );
}
