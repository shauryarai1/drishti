'use client';

import React from 'react';
import { GoogleAuthButton } from './GoogleAuthButton';
import { loginHref } from '../lib/authPaths';

/**
 * The result gate.
 *
 * A guest may open a tool and fill the form; this gate appears only where the
 * personalised RESULT would be revealed. It never blocks the form itself.
 * The pending form is preserved separately (see lib/pendingForms), so nothing
 * has to be retyped after signing in.
 */

interface ResultGateProps {
  /** Internal KAVACH path to return to after authentication. */
  nextPath: string;
  title?: string;
  body?: string;
}

export function ResultGate({
  nextPath,
  title = 'SAVE & VIEW YOUR READING',
  body = 'Sign in to view your personalized result and keep it safely in My KAVACH.',
}: ResultGateProps) {
  return (
    <section className="rounded-xl border border-[#A62A34]/30 bg-[#160A0C]/80 p-6 sm:p-8">
      <h2 className="text-xl font-semibold tracking-tight text-[#F7F5F0] sm:text-2xl">{title}</h2>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-[#EEE9DF]/70">{body}</p>

      <div className="mt-6 max-w-sm">
        <GoogleAuthButton nextPath={nextPath} />
        <a
          href={loginHref(nextPath)}
          className="mt-3 inline-flex h-11 w-full items-center justify-center rounded border border-[#B39250]/40 bg-[#B39250]/15 px-5 font-mono text-[11px] uppercase tracking-[0.18em] text-[#D6BE85] transition-colors hover:bg-[#B39250]/25"
        >
          CONTINUE WITH EMAIL
        </a>
      </div>
    </section>
  );
}
