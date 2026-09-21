'use client';

import React, { useState } from 'react';
import { AUTH_INPUT, AUTH_LABEL, AuthShell } from '../../components/AuthShell';
import { useAuth } from '../../lib/auth';

export default function ForgotPasswordPage() {
  const { sendPasswordReset } = useAuth();
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setError('');
    setNotice('');

    if (!email.trim()) {
      setError('Enter the email address for your account.');
      return;
    }

    setBusy(true);
    const result = await sendPasswordReset(email, `${window.location.origin}/reset-password`);
    setBusy(false);

    if (!result.ok) {
      setError(result.message ?? 'We could not send a reset link. Please try again.');
      return;
    }
    setNotice(result.message ?? 'If that email is registered, a reset link is on its way.');
  };

  return (
    <AuthShell
      label="KAVACH · Accounts"
      title="RESET PASSWORD"
      subtitle="Enter your email and we will send you a secure link to choose a new password."
      footer={
        <>
          <a href="/login" className="text-[#D6BE85] hover:text-[#F7F5F0]">Back to sign in</a>
        </>
      }
    >
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
          {busy ? 'Sending…' : 'Send reset link'}
        </button>
      </form>
    </AuthShell>
  );
}
