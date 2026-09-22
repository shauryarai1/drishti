'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AUTH_INPUT, AUTH_LABEL, AuthShell } from '../../components/AuthShell';
import { AuthOrDivider, GoogleAuthButton } from '../../components/GoogleAuthButton';
import { useAuth } from '../../lib/auth';
import { safeNextPath } from '../../lib/authPaths';

const MIN_PASSWORD = 8;

export default function SignupPage() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [next, setNext] = useState('/account');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setNext(safeNextPath(params.get('next')));
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setError('');
    setNotice('');

    if (!email.trim()) {
      setError('Enter a valid email address.');
      return;
    }
    if (password.length < MIN_PASSWORD) {
      setError(`Choose a password of at least ${MIN_PASSWORD} characters.`);
      return;
    }
    if (password !== confirm) {
      setError('Those passwords do not match.');
      return;
    }

    setBusy(true);
    const result = await signUp(email, password);
    setBusy(false);

    if (!result.ok) {
      setError(result.message ?? 'We could not create your account. Please try again.');
      return;
    }
    if (result.message) {
      setNotice(result.message);
      return;
    }
    router.replace(next);
  };

  return (
    <AuthShell
      label="KAVACH · Accounts"
      title="CREATE ACCOUNT"
      subtitle="An account keeps your charts and readings available to you alone."
      footer={
        <>
          Already have an account?{' '}
          <a href="/login" className="text-[#D6BE85] hover:text-[#F7F5F0]">Sign in</a>
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
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className={`mt-1.5 ${AUTH_INPUT}`}
          />
          <p className="mt-1.5 text-[11px] text-[#EEE9DF]/40">At least {MIN_PASSWORD} characters.</p>
        </div>
        <div>
          <label className={AUTH_LABEL} htmlFor="confirm">Confirm password</label>
          <input
            id="confirm"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            className={`mt-1.5 ${AUTH_INPUT}`}
          />
        </div>

        {error && (
          <div role="alert" className="rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12.5px] text-[#EEE9DF]/80">
            {error}
          </div>
        )}
        {notice && (
          <div role="status" className="rounded border border-[#B39250]/40 bg-[#B39250]/10 p-3 text-[12.5px] text-[#D6BE85]">
            {notice}
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded bg-[#7B1D26] px-5 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  );
}
