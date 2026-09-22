'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AUTH_INPUT, AUTH_LABEL, AuthShell } from '../../components/AuthShell';
import { AuthOrDivider, GoogleAuthButton } from '../../components/GoogleAuthButton';
import { useAuth } from '../../lib/auth';
import { safeNextPath } from '../../lib/authPaths';

export default function LoginPage() {
  const router = useRouter();
  const { status, signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [next, setNext] = useState('/account');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setNext(safeNextPath(params.get('next')));
  }, []);

  useEffect(() => {
    if (status === 'signedIn') router.replace(next);
  }, [status, next, router]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setError('');

    if (!email.trim() || !password) {
      setError('Enter your email and password to continue.');
      return;
    }

    setBusy(true);
    const result = await signIn(email, password);
    setBusy(false);

    if (!result.ok) {
      setError(result.message ?? 'We could not sign you in. Please try again.');
      return;
    }
    router.replace(next);
  };

  return (
    <AuthShell
      label="KAVACH · Accounts"
      title="SIGN IN"
      subtitle="Sign in to save charts and readings to your private history."
      footer={
        <>
          No account yet?{' '}
          <a href="/signup" className="text-[#D6BE85] hover:text-[#F7F5F0]">Create account</a>
          {' · '}
          <a href="/forgot-password" className="text-[#EEE9DF]/60 hover:text-[#F7F5F0]">Forgot password?</a>
        </>
      }
    >
      <GoogleAuthButton nextPath={next} />
      <AuthOrDivider />

      <form onSubmit={submit} className="space-y-4" noValidate>
        <div>
          <label className={AUTH_LABEL} htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className={`mt-1.5 ${AUTH_INPUT}`}
          />
        </div>
        <div>
          <label className={AUTH_LABEL} htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className={`mt-1.5 ${AUTH_INPUT}`}
          />
        </div>

        {error && (
          <div role="alert" className="rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12.5px] text-[#EEE9DF]/80">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded bg-[#7B1D26] px-5 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? 'Signing in…' : 'Log in'}
        </button>
      </form>
    </AuthShell>
  );
}
