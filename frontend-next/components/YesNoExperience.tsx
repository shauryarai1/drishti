'use client';

import React, { useRef, useState } from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Button } from './Button';
import { Header } from './Header';
import { Footer } from './Footer';
import { API_BASE } from '../lib/api';

type Phase = 'idle' | 'loading' | 'done' | 'error';

interface Verdict {
  /** 'YES' | 'NO' | '50/50', or null when a safety message is returned instead. */
  verdict: string | null;
  interpretation: string;
}

const MAX_QUESTION = 300;

const VERDICT_STYLES: Record<string, string> = {
  YES: 'text-[#D6BE85]',
  NO: 'text-[#EEE9DF]/85',
  '50/50': 'text-[#EEE9DF]/85',
};

function verdictSize(verdict: string | null): string {
  if (verdict === '50/50') return 'text-4xl sm:text-5xl md:text-6xl';
  return 'text-6xl sm:text-7xl md:text-8xl';
}

/**
 * KAVACH SANKET experience.
 *
 * The verdict comes entirely from the deterministic backend, computed from the
 * exact local time the question is submitted. This component only displays the
 * result: it never computes, alters or second-guesses the verdict, and it never
 * shows the internal arithmetic or how the verdict was derived.
 *
 * It renders the page chrome too, so the /yes-no route keeps a server component
 * (and therefore its metadata) while the interactive parts stay on the client.
 */
export function YesNoExperience() {
  const [question, setQuestion] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<Verdict | null>(null);
  const [error, setError] = useState('');
  const submitting = useRef(false);

  const trimmed = question.trim();
  const canSubmit = trimmed.length >= 3 && phase !== 'loading';

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    // Guard against a double submission from a double tap or a held Enter key.
    if (submitting.current || !canSubmit) return;
    submitting.current = true;

    setPhase('loading');
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/yes-no`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmed,
          // The exact moment the question was asked, in the user's own timezone.
          timestamp: new Date().toISOString(),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
        }),
      });

      if (!response.ok) throw new Error('request failed');

      const body = await response.json();
      if (body?.status !== 'ok' || typeof body?.interpretation !== 'string') {
        throw new Error('invalid response');
      }

      setResult({ verdict: body.verdict ?? null, interpretation: body.interpretation });
      setPhase('done');
    } catch {
      setError("We couldn't reach KAVACH just now. Please try again in a moment.");
      setPhase('error');
    } finally {
      submitting.current = false;
    }
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF]">
      <Header onStartReading={() => { window.location.href = '/'; }} />

      <div className="architectural-grid border-b border-[#A62A34]/20 bg-[#160A0C]">
        <Container size="md" className="py-12 sm:py-16">
          <div className="text-center">
            <SectionLabel label="ASK THE MOMENT" tone="brass" className="justify-center" />
            <h1 className="mt-6 text-2xl font-semibold tracking-[0.08em] text-[#F7F5F0] sm:text-3xl md:text-4xl">
              KAVACH SANKET
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-[#EEE9DF]/70 sm:text-base">
              Ask one clear question. KAVACH reads the moment and gives you a simple indication.
            </p>
          </div>

      <form onSubmit={submit} className="mx-auto mt-10 max-w-2xl">
        <label
          htmlFor="yesno-question"
          className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]"
        >
          Your question
        </label>
        <p className="mt-2 text-[11px] text-[#EEE9DF]/45">
          Focus on one question before revealing your Sanket.
        </p>
        <textarea
          id="yesno-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value.slice(0, MAX_QUESTION))}
          rows={3}
          placeholder="Will my business deal work?"
          disabled={phase === 'loading'}
          className="mt-3 w-full resize-none rounded-lg border border-[#A62A34]/30 bg-[#160A0C]/70 px-4 py-3.5 text-[15px] leading-relaxed text-[#F7F5F0] placeholder:text-[#EEE9DF]/30 focus:border-[#B39250]/50 focus:outline-none disabled:opacity-60"
        />

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="text-[11px] text-[#EEE9DF]/40">
            {trimmed.length < 3 ? 'Type at least a few words.' : `${trimmed.length}/${MAX_QUESTION}`}
          </span>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={!canSubmit}
            className="w-full sm:w-auto"
          >
            {phase === 'loading' ? 'Reading the moment…' : 'REVEAL ANSWER'}
          </Button>
        </div>
      </form>

      <div aria-live="polite" className="mx-auto mt-10 max-w-2xl">
        {phase === 'error' && (
          <div className="rounded-lg border border-[#A62A34]/30 bg-[#160A0C]/60 px-6 py-6">
            <p className="text-sm leading-relaxed text-[#EEE9DF]/80">{error}</p>
          </div>
        )}

        {phase === 'loading' && (
          <div className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/50 px-6 py-8 text-center">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-[#B39250]">
              Reading the moment
            </p>
            <p className="mt-3 text-sm text-[#EEE9DF]/60">Please wait a moment.</p>
          </div>
        )}

        {phase === 'done' && result && (
          <div className="rounded-xl border border-[#A62A34]/40 bg-gradient-to-b from-[#2B0C11]/90 via-[#160A0C] to-[#090909] px-6 py-10 shadow-[0_24px_80px_rgba(0,0,0,0.85)] sm:px-10 sm:py-12">
            {result.verdict ? (
              <>
                <p className="text-center font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
                  The indication
                </p>
                <p
                  className={`mt-4 text-center font-semibold tracking-tight ${verdictSize(
                    result.verdict,
                  )} ${VERDICT_STYLES[result.verdict] ?? 'text-[#EEE9DF]/85'}`}
                >
                  {result.verdict}
                </p>
                <div className="mx-auto mt-8 h-[1px] w-16 bg-[#A62A34]/40" />
              </>
            ) : (
              <p className="text-center font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
                A note before anything else
              </p>
            )}

            <p className="mt-8 text-[15px] leading-relaxed text-[#EEE9DF]/85 sm:text-base">
              {result.interpretation}
            </p>

            <p className="mt-8 border-t border-[#A62A34]/20 pt-5 text-[11px] leading-relaxed text-[#EEE9DF]/45">
              Astrological guidance is a matter of personal belief and is not a guarantee of any
              outcome. Decisions you take remain your own.
            </p>
          </div>
        )}
        </div>
        </Container>
      </div>

      <Footer />
    </main>
  );
}
