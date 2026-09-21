'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { useAuth } from '../../lib/auth';

function createdDate(value: string | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' });
}

export default function AccountPage() {
  const router = useRouter();
  const { status, user, signOut, configured } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    router.replace('/');
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-10 sm:py-16">
        <div className="mx-auto w-full max-w-[560px]">
          <MaskedReveal>
            <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">KAVACH · Accounts</div>
            <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">ACCOUNT</h1>
          </MaskedReveal>

          {!configured && (
            <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 text-[13px] text-[#EEE9DF]/60">
              Accounts are not enabled on this deployment yet.
            </div>
          )}

          {configured && status === 'loading' && (
            <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#B39250]">Loading your account</div>
              <p className="mt-1 text-[13px] text-[#EEE9DF]/55">Checking your session&hellip;</p>
            </div>
          )}

          {configured && status === 'signedOut' && (
            <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
              <p className="text-[13px] text-[#EEE9DF]/70">You are not signed in.</p>
              <div className="mt-4 flex flex-wrap gap-2.5">
                <a
                  href="/login"
                  className="inline-flex h-9 items-center rounded border border-[#A62A34]/40 px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/85 transition-colors hover:border-[#A62A34]/70 hover:text-[#F7F5F0]"
                >
                  Sign in
                </a>
                <a
                  href="/signup"
                  className="inline-flex h-9 items-center rounded bg-[#7B1D26] px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
                >
                  Create account
                </a>
              </div>
            </div>
          )}

          {configured && status === 'signedIn' && user && (
            <div className="mt-6 space-y-4">
              <div className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
                <div className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">Email</div>
                <div className="mt-1 break-all text-[14px] text-[#F7F5F0]">{user.email}</div>

                <div className="mt-4 font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">Account created</div>
                <div className="mt-1 text-[14px] text-[#EEE9DF]/80">{createdDate(user.created_at)}</div>
              </div>

              <a
                href="/history"
                className="block rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 transition-colors hover:border-[#A62A34]/50"
              >
                <div className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">History</div>
                <div className="mt-1 text-[14px] text-[#EEE9DF]/85">Your saved charts and readings</div>
              </a>

              <button
                type="button"
                onClick={handleSignOut}
                className="inline-flex h-9 items-center rounded border border-[#A62A34]/40 px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/85 transition-colors hover:border-[#A62A34]/70 hover:text-[#F7F5F0] cursor-pointer"
              >
                Log out
              </button>

              <p className="pt-1 text-[11.5px] leading-relaxed text-[#EEE9DF]/40">
                Your birth details and readings are private to your account.
              </p>
            </div>
          )}
        </div>
      </Container>
    </main>
  );
}
