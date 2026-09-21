'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AUTH_INPUT, AUTH_LABEL, AuthShell } from '../../components/AuthShell';
import { useAuth } from '../../lib/auth';

const MIN_PASSWORD = 8;

export default function ResetPasswordPage() {
  const router = useRouter();
  const { status, updatePassword } = useAuth();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setError('');
    setNotice('');

    if (password.length < MIN_PASSWORD) {
      setError(`Choose a password of at least ${MIN_PASSWORD} characters.`);
      return;
    }
    if (password !== confirm) {
      setError('Those passwords do not match.');
      return;
    }

    setBusy(true);
    const result = await updatePassword(password);
    setBusy(false);

    if (!result.ok) {
      setError(result.message ?? 'We could not update your password. Please try again.');
      return;
    }
    setNotice(result.message ?? 'Your password has been updated.');
    setPassword('');
    setConfirm('');
    setTimeout(() => router.replace('/account'), 1200);
  };

  return (
    <AuthShell
      label="KAVACH · Accounts"
      title="CHOOSE A NEW PASSWORD"
      subtitle="Set a new password for your KAVACH account."
      footer={
        <>
          <a href="/forgot-password" className="text-[#EEE9DF]/60 hover:text-[#F7F5F0]">Request a new link</a>
        </>
      }
    >
      {status === 'loading' && (
        <p className="text-[13px] text-[#EEE9DF]/55">Preparing your secure session…</p>
      )}

      {status === 'signedOut' && (
        <div className="space-y-3">
          <p className="text-[13px] leading-relaxed text-[#EEE9DF]/70">
            This reset link is invalid or has expired.
          </p>
          <a
            href="/forgot-password"
            className="inline-flex h-10 items-center justify-center rounded bg-[#7B1D26] px-5 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
          >
            Send a new link
          </a>
        </div>
      )}

      {status === 'signedIn' && (
        <form onSubmit={submit} className="space-y-4" noValidate>
          <div>
            <label className={AUTH_LABEL} htmlFor="password">New password</label>
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
            <label className={AUTH_LABEL} htmlFor="confirm">Confirm new password</label>
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
            {busy ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
