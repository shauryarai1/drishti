'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { useAuth } from '../lib/auth';
import { loginHref, safeNextPath } from '../lib/authPaths';
import { getPrimaryProfile, type BirthProfile } from '../lib/profiles';

/**
 * The shared two-gate guard.
 *
 *   GATE 1  authenticated?          no -> login (with a validated return path)
 *   GATE 2  Primary Profile exists? no -> /profile/setup (unless this surface
 *                                          only needs authentication)
 *
 * States are explicit so a network/database FAILURE is never mistaken for a
 * missing profile: a failed load shows a retry state and never redirects to
 * setup. Latest-wins protects against a stale profile response.
 */

type ProfileState = 'idle' | 'loading' | 'ready' | 'missing' | 'error';

interface RequireProfileProps {
  children: React.ReactNode;
  /** false = login only; the Primary Profile must not gate this surface. */
  requireProfile?: boolean;
}

export function RequireProfile({ children, requireProfile = true }: RequireProfileProps) {
  const { status, user, configured } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<ProfileState>('idle');
  const [primary, setPrimary] = useState<BirthProfile | null>(null);
  const [error, setError] = useState('');
  const requestIdRef = useRef(0);

  const loadProfile = useCallback(async (userId: string) => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setState('loading');
    setError('');
    try {
      const profile = await getPrimaryProfile(userId);
      if (requestId !== requestIdRef.current) return;
      setPrimary(profile);
      setState(profile ? 'ready' : 'missing');
    } catch {
      if (requestId !== requestIdRef.current) return;
      // PROFILE_LOAD_FAILED is NOT PROFILE_NOT_FOUND: never send to setup here.
      setState('error');
      setError('We could not load your profile just now.');
    }
  }, []);

  useEffect(() => {
    if (status === 'loading') return;
    if (status !== 'signedIn' || !user) {
      setState('idle');
      return;
    }
    if (!requireProfile) {
      setState('ready');
      return;
    }
    void loadProfile(user.id);
  }, [status, user, requireProfile, loadProfile]);

  const next = safeNextPath(pathname);

  useEffect(() => {
    if (state === 'missing') router.replace(`/profile/setup?next=${encodeURIComponent(next)}`);
  }, [state, next, router]);

  if (!configured) {
    return <Notice title="Accounts are not available here yet" body="Please try again later." />;
  }

  // Only an unresolved AUTH state is "checking your session". A resolved
  // signed-out state must fall through to the sign-in notice below (the old
  // `state === 'idle'` clause here pinned signed-out users on this screen
  // forever, because 'idle' never changes once the session resolves).
  if (status === 'loading') {
    return <Notice title="Loading" body="Checking your session…" />;
  }

  if (status !== 'signedIn' || !user) {
    return (
      <Notice
        title="Sign in required"
        body="KAVACH personal readings are tied to your account."
        action={{ label: 'SIGN IN', href: loginHref(pathname) }}
      />
    );
  }

  if (requireProfile && state === 'error') {
    return (
      <Notice
        title="We could not load your profile"
        body={error || 'Please try again.'}
        action={{ label: 'RETRY', onClick: () => void loadProfile(user.id) }}
      />
    );
  }

  if (requireProfile && state !== 'ready') {
    return <Notice title="Loading" body="Preparing your profile…" />;
  }

  return (
    <>
      {requireProfile && primary ? (
        <div className="sr-only" data-profile-ready={primary.id} />
      ) : null}
      {children}
    </>
  );
}

function Notice({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: { label: string; href?: string; onClick?: () => void };
}) {
  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Container size="md" className="py-16 sm:py-24">
        <SectionLabel label="KAVACH · Accounts" tone="brass" />
        <h1 className="mt-3 text-xl font-semibold text-[#F7F5F0] sm:text-2xl">{title}</h1>
        <p className="mt-2 max-w-xl text-[13.5px] leading-relaxed text-[#EEE9DF]/60">{body}</p>
        {action && (
          <div className="mt-6">
            {action.href ? (
              <a
                href={action.href}
                className="inline-flex h-11 items-center justify-center rounded bg-[#7B1D26] px-6 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
              >
                {action.label}
              </a>
            ) : (
              <button
                type="button"
                onClick={action.onClick}
                className="inline-flex h-11 items-center justify-center rounded border border-[#B39250]/40 bg-[#B39250]/15 px-6 font-mono text-[11px] uppercase tracking-[0.18em] text-[#D6BE85] transition-colors hover:bg-[#B39250]/25"
              >
                {action.label}
              </button>
            )}
          </div>
        )}
      </Container>
    </main>
  );
}
