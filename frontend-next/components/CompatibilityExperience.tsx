'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { API_BASE, api } from '../lib/api';
import { authHeaders } from '../lib/authHeaders';
import { useAuth } from '../lib/auth';
import { isValidPersonName, normalisePersonName } from '../lib/personName';
import {
  getReading,
  saveCompatibilityReading,
  type CompatibilityHistoryInput,
} from '../lib/history';

interface Profile {
  name: string;
  date: string;
  time: string;
  place: string;
  lat?: number;
  lon?: number;
  tz?: string;
}

interface Factor {
  key: string;
  label: string;
  subtitle: string;
  status: string;
  summary: string;
  facts: Record<string, unknown>;
}

interface Report {
  /** Interpreted report (current). */
  overall?: { state: string; summary: string };
  atAGlance?: Array<{ category: string; status: string; interpretation: string }>;
  strengths?: string[];
  attentionAreas?: string[];
  inDepth?: Array<{ category: string; interpretation: string }>;
  kavachView?: string;
  /** Layer 2: the openly displayed astrological working (approved fields only). */
  technicalAnalysis?: Array<{
    factor: string;
    values: Record<string, unknown>;
    result: string;
    meaning: string;
    matched?: boolean;
    points?: number;
    maximum?: number;
  }>;
  totalScore?: {
    awarded: number;
    maximum: number;
    factors: Array<{ factor: string; matched: boolean; points: number; maximum: number }>;
    outOf36: boolean;
    unscored: Array<{ factor: string; reason: string }>;
  };
  overallWorking?: {
    state: string;
    counts: Record<string, number>;
    eligible: Array<{ factor: string; result: string }>;
    contextualOnly: Array<{ factor: string; result: string }>;
    note: string;
  };
  /** Legacy V1 shape (older saved reports): rendered safely, never recalculated. */
  factors?: Array<{ label: string; subtitle: string; status: string; summary: string }>;
  label?: string;
  summary?: string;
  disclaimer?: string;
}

interface PersonView {
  role: string;
  name: string;
  moonSign: string;
  moonNakshatra: string;
}

const EMPTY: Profile = { name: '', date: '', time: '', place: '' };

const STATUS_STYLE: Record<string, string> = {
  'Strong alignment': 'border-[#B39250]/50 bg-[#B39250]/10 text-[#D6BE85]',
  Supportive: 'border-[#7BD88F]/30 bg-[#7BD88F]/10 text-[#9BE0AB]',
  Mixed: 'border-[#EEE9DF]/20 bg-[#EEE9DF]/5 text-[#EEE9DF]/75',
  'Needs attention': 'border-[#E5B567]/35 bg-[#E5B567]/10 text-[#E5B567]',
};

const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5';
const FIELD =
  'mt-1 w-full rounded border border-[#A62A34]/35 bg-[#0E0708] px-3 py-2.5 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';
const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

export function CompatibilityExperience() {
  const { status: authStatus, user } = useAuth();
  const [bride, setBride] = useState<Profile>(EMPTY);
  const [groom, setGroom] = useState<Profile>(EMPTY);
  const [report, setReport] = useState<Report | null>(null);
  const [people, setPeople] = useState<PersonView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const savedSignatureRef = useRef<string | null>(null);
  const submittingRef = useRef(false);

  const payload = (p: Profile) => ({
    name: normalisePersonName(p.name),
    date: p.date,
    time: p.time,
    place: p.place,
    latitude: p.lat ?? null,
    longitude: p.lon ?? null,
    timezone: p.tz ?? '',
  });

  const historyInput = (): CompatibilityHistoryInput => ({
    bride_name: normalisePersonName(bride.name),
    bride_date: bride.date,
    bride_time: bride.time,
    bride_place: bride.place,
    bride_latitude: bride.lat,
    bride_longitude: bride.lon,
    bride_timezone: bride.tz,
    groom_name: normalisePersonName(groom.name),
    groom_date: groom.date,
    groom_time: groom.time,
    groom_place: groom.place,
    groom_latitude: groom.lat,
    groom_longitude: groom.lon,
    groom_timezone: groom.tz,
  });

  const validate = (): string => {
    if (!isValidPersonName(bride.name)) return "Please enter the bride's name.";
    if (!bride.date || !bride.time || !bride.place.trim()) return "Please complete the bride's birth date, time and place.";
    if (!isValidPersonName(groom.name)) return "Please enter the groom's name.";
    if (!groom.date || !groom.time || !groom.place.trim()) return "Please complete the groom's birth date, time and place.";
    return '';
  };

  const autoSave = async (nextPeople: PersonView[], nextReport: Report) => {
    if (!user) return;
    const signature = JSON.stringify(historyInput());
    if (savedSignatureRef.current === signature) return;
    savedSignatureRef.current = signature;
    try {
      await saveCompatibilityReading(user.id, historyInput(), { people: nextPeople, report: nextReport });
      setNotice('Saved to My KAVACH.');
    } catch (exc) {
      savedSignatureRef.current = null;
      setNotice(exc instanceof Error ? exc.message : '');
    }
  };

  const run = async (nextBride: Profile, nextGroom: Profile) => {
    setBusy(true);
    setError('');
    setReport(null);
    try {
      const identity = await authHeaders();
      const response = await fetch(`${API_BASE}/compatibility`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...identity },
        body: JSON.stringify({ bride: payload(nextBride), groom: payload(nextGroom) }),
      });
      const body = await response.json();
      if (!response.ok || body.status !== 'ok') {
        throw new Error(body.message || "We couldn't prepare this matchmaking report.");
      }
      setPeople(body.people as PersonView[]);
      setReport(body.report as Report);
      void autoSave(body.people as PersonView[], body.report as Report);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "We couldn't prepare this matchmaking report.");
    } finally {
      setBusy(false);
      submittingRef.current = false;
    }
  };

  const submit = async () => {
    if (submittingRef.current || busy) return;
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    // Public: a guest checks compatibility immediately. Saving to My KAVACH is
    // the only account-gated step, and it never runs for a guest (see autoSave).
    submittingRef.current = true;
    await run(bride, groom);
  };

  // Open a saved report from My KAVACH. Only meaningful for a signed-in account.
  useEffect(() => {
    if (authStatus !== 'signedIn' || !user) return;
    const params = new URLSearchParams(window.location.search);
    const savedId = params.get('saved');
    if (!savedId) return;
    (async () => {
      try {
        const reading = await getReading(user.id, savedId);
        const stored = reading?.result_data as { people?: PersonView[]; report?: Report } | undefined;
        if (reading?.type !== 'compatibility' || !stored?.report) {
          setError('That saved matchmaking report could not be found.');
          return;
        }
        setPeople(stored.people ?? []);
        setReport(stored.report);
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : 'We could not open that saved report.');
      }
    })();
  }, [authStatus, user]);

  const ready = report !== null;

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="lg" className="py-10 sm:py-14">
        <SectionLabel label="KAVACH · Matchmaking" tone="brass" />
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-4xl">
          MATCHMAKING
        </h1>
        <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-[#EEE9DF]/55">
          Traditional compatibility analysis built around Kuta matching. Some rules are
          directional, so both matching roles are entered separately.
        </p>

        {!ready && (
          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            <ProfileCard title="Bride" profile={bride} onChange={setBride} />
            <ProfileCard title="Groom" profile={groom} onChange={setGroom} />
          </div>
        )}

        {!ready && (
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              type="button"
              onClick={() => void submit()}
              disabled={busy}
              className="inline-flex h-11 items-center justify-center rounded bg-[#7B1D26] px-8 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50"
            >
              {busy ? 'Preparing…' : 'Check match'}
            </button>
            <span className="text-[11px] text-[#EEE9DF]/40">
              Guest-friendly: you can fill both profiles before signing in.
            </span>
          </div>
        )}

        {error && (
          <div role="alert" className="mt-4 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
            {error}
          </div>
        )}

        {ready && report && (
          <div className="mt-8">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-[#F7F5F0] sm:text-2xl">
                {people.find((p) => p.role === 'bride')?.name} <span className="text-[#A62A34]">×</span>{' '}
                {people.find((p) => p.role === 'groom')?.name}
              </h2>
            </div>

            {report.overall ? (
              <InterpretedReport report={report} />
            ) : report.factors ? (
              <LegacyReport report={report} />
            ) : null}

            {notice && <p className="mt-3 text-[12px] text-[#D6BE85]">{notice}</p>}

            <div className="mt-6 flex flex-wrap items-center gap-4">
              <a href="/history" className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#D6BE85] hover:text-[#F7F5F0]">
                View in My KAVACH
              </a>
              <button
                type="button"
                onClick={() => { setReport(null); setPeople([]); setNotice(''); setBride(EMPTY); setGroom(EMPTY); }}
                className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/50 hover:text-[#D6BE85]"
              >
                New check
              </button>
            </div>
          </div>
        )}

      </Container>
      <Footer />
    </main>
  );
}

/** The interpreted, customer-facing report. No technique is ever shown. */
function InterpretedReport({ report }: { report: Report }) {
  return (
    <div className="mt-6 space-y-10">
      {report.technicalAnalysis && report.technicalAnalysis.length > 0 && (
        <details className="rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/50 p-5 sm:p-6">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
            How Kavach analysed this match
          </summary>
          <div className="mt-5 space-y-5">
            {report.totalScore && (
              <div className="rounded-lg border border-[#B39250]/30 bg-[#090909]/50 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className={SECTION}>Traditional score</span>
                  <span className="font-mono text-[15px] text-[#D6BE85]">
                    TOTAL: {report.totalScore.awarded} / {report.totalScore.maximum}
                  </span>
                </div>
                <p className="mt-2 text-[11.5px] leading-relaxed text-[#EEE9DF]/50">
                  Each factor is either a full match or no match — there are no partial points.
                  {report.totalScore.unscored.length > 0 && (
                    <> {' '}Not scored: {report.totalScore.unscored.map((row) => row.factor).join(', ')}.</>
                  )}
                </p>
              </div>
            )}
            {report.technicalAnalysis.map((entry, index) => (
              <article key={index} className="border-l border-[#A62A34]/30 pl-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-[13px] font-semibold tracking-[0.06em] text-[#F7F5F0]">
                    {entry.factor}
                  </h4>
                  <div className="flex items-center gap-2">
                    {typeof entry.matched === 'boolean' && (
                      <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[#EEE9DF]/55">
                        {entry.matched ? 'MATCH' : 'NO MATCH'}
                      </span>
                    )}
                    <span
                      className={`rounded border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em] ${
                        STATUS_STYLE[entry.result] ?? STATUS_STYLE.Mixed
                      }`}
                    >
                      {entry.result}
                    </span>
                  </div>
                </div>
                {typeof entry.points === 'number' && (
                  <div className="mt-1 font-mono text-[11px] text-[#D6BE85]">
                    Points: {entry.points} / {entry.maximum}
                  </div>
                )}
                <dl className="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2">
                  {Object.entries(entry.values).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-3 text-[12.5px]">
                      <dt className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#EEE9DF]/45">
                        {key.replace(/([A-Z])/g, ' $1')}
                      </dt>
                      <dd className="text-[#EEE9DF]/85">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
                <p className="mt-2 text-[13px] leading-relaxed text-[#EEE9DF]/70">
                  <span className="text-[#D6BE85]">What this means: </span>
                  {entry.meaning}
                </p>
              </article>
            ))}
          </div>
        </details>
      )}

      {/* HERO: the Kuta Match Score is the primary product. */}
      <section className="rounded-xl border border-[#B39250]/35 bg-gradient-to-b from-[#2B0C11]/85 to-[#090909] p-6 text-center sm:p-9">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">Match Score</div>
        {report.totalScore ? (
          <div className="mt-4 flex items-end justify-center gap-2">
            <span className="text-5xl font-semibold tracking-[0.02em] text-[#F7F5F0] sm:text-6xl">
              {report.totalScore.awarded}
            </span>
            <span className="pb-1 font-mono text-[15px] text-[#EEE9DF]/55 sm:pb-2">
              / {report.totalScore.maximum}
            </span>
          </div>
        ) : (
          <div className="mt-4 text-3xl font-semibold tracking-[0.06em] text-[#F7F5F0]">
            {report.overall?.state}
          </div>
        )}
        <div className="mt-4 text-xl font-semibold tracking-[0.06em] text-[#D6BE85] sm:text-2xl">
          {report.overall?.state}
        </div>
        <p className="mx-auto mt-3 max-w-2xl text-[14px] leading-relaxed text-[#EEE9DF]/80">
          {report.overall?.summary}
        </p>
        <p className="mx-auto mt-3 max-w-2xl text-[12px] leading-relaxed text-[#EEE9DF]/50">
          KAVACH compares the traditional matching factors individually and combines the scored
          factors into the Match Score. This is traditional guidance, not a decision.
        </p>
      </section>

      {/* KUTA MATCHING TABLE: directly under the score. */}
      {report.totalScore && (
        <section>
          <h3 className={SECTION}>Kuta matching</h3>
          <div className="mt-4 overflow-hidden rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70">
            <div className="flex items-center justify-between gap-3 border-b border-[#A62A34]/20 px-4 py-2.5 font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#B39250]">
              <span>Factor</span>
              <span className="flex shrink-0 gap-4">
                <span className="w-16 text-right">Result</span>
                <span className="w-14 text-right">Score</span>
              </span>
            </div>
            <ul>
              {report.totalScore.factors.map((row) => (
                <li
                  key={row.factor}
                  className="flex items-center justify-between gap-3 border-b border-[#A62A34]/10 px-4 py-3 last:border-b-0"
                >
                  <span className="min-w-0 text-[13.5px] text-[#F7F5F0]">{row.factor}</span>
                  <span className="flex shrink-0 gap-4">
                    <span
                      className={`w-16 text-right font-mono text-[10px] uppercase tracking-[0.1em] ${
                        row.matched ? 'text-[#9BE0AB]' : 'text-[#EEE9DF]/55'
                      }`}
                    >
                      {row.matched ? 'Match' : 'No Match'}
                    </span>
                    <span className="w-14 text-right font-mono text-[12px] text-[#D6BE85]">
                      {row.points} / {row.maximum}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between gap-3 bg-[#090909]/60 px-4 py-3.5">
              <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-[#B39250]">Total</span>
              <span className="font-mono text-[16px] text-[#F7F5F0]">
                {report.totalScore.awarded} / {report.totalScore.maximum}
              </span>
            </div>
          </div>
          {report.totalScore.unscored.length > 0 && (
            <p className="mt-2 text-[11.5px] leading-relaxed text-[#EEE9DF]/45">
              Each factor is either a full match or no match — there are no partial points.{' '}
              Not scored: {report.totalScore.unscored.map((row) => row.factor).join(', ')}.
            </p>
          )}
        </section>
      )}

      <section>
        <h3 className={SECTION}>Deeper match analysis</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {report.atAGlance?.map((entry, index) => (
            <div key={index} className="rounded-lg border border-[#A62A34]/20 bg-[#160A0C]/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="text-[13px] font-medium text-[#F7F5F0]">{entry.category}</div>
                <span
                  className={`shrink-0 rounded border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em] ${
                    STATUS_STYLE[entry.status] ?? STATUS_STYLE.Mixed
                  }`}
                >
                  {entry.status}
                </span>
              </div>
              <p className="mt-2 text-[12.5px] leading-relaxed text-[#EEE9DF]/65">
                {entry.interpretation}
              </p>
            </div>
          ))}
        </div>
      </section>

      {report.strengths && report.strengths.length > 0 && (
        <section>
          <h3 className={SECTION}>What works well</h3>
          <ul className="mt-4 space-y-2">
            {report.strengths.map((item) => (
              <li key={item} className="flex items-start gap-3 text-[14px] text-[#EEE9DF]/80">
                <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rotate-45 border border-[#B39250]/70 bg-[#7B1D26]/60" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3 className={SECTION}>What needs attention</h3>
        {report.attentionAreas && report.attentionAreas.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {report.attentionAreas.map((item) => (
              <li key={item} className="flex items-start gap-3 text-[14px] text-[#EEE9DF]/80">
                <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rotate-45 border border-[#A62A34]/70 bg-[#A62A34]/40" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-[14px] text-[#EEE9DF]/60">
            Nothing here stands out as needing particular attention.
          </p>
        )}
      </section>

      <section>
        <h3 className={SECTION}>In-depth match analysis</h3>
        <div className="mt-4 space-y-6">
          {report.inDepth?.map((entry, index) => (
            <article key={index} className="border-l border-[#A62A34]/30 pl-4 sm:pl-5">
              <h4 className="text-[13px] font-medium uppercase tracking-[0.12em] text-[#D6BE85]">
                {entry.category}
              </h4>
              <p className="mt-2 text-[14px] leading-relaxed text-[#EEE9DF]/80">
                {entry.interpretation}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-[#A62A34]/30 bg-[#160A0C]/70 p-6 sm:p-7">
        <h3 className={SECTION}>Kavach view</h3>
        <p className="mt-3 text-[15px] leading-relaxed text-[#EEE9DF]/85">{report.kavachView}</p>
      </section>

      {report.overallWorking && (
        <details className="rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/50 p-5 sm:p-6">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
            Why this overall result?
          </summary>
          <p className="mt-4 text-[13px] leading-relaxed text-[#EEE9DF]/70">
            {report.overallWorking.note}
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <div className={SECTION}>Counted towards the assessment</div>
              <ul className="mt-2 space-y-1">
                {report.overallWorking.eligible.map((row, index) => (
                  <li key={index} className="flex justify-between gap-3 text-[12.5px] text-[#EEE9DF]/80">
                    <span>{row.factor}</span>
                    <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#D6BE85]">
                      {row.result}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className={SECTION}>Contextual only</div>
              {report.overallWorking.contextualOnly.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {report.overallWorking.contextualOnly.map((row, index) => (
                    <li key={index} className="flex justify-between gap-3 text-[12.5px] text-[#EEE9DF]/60">
                      <span>{row.factor}</span>
                      <span className="font-mono text-[10px] uppercase tracking-[0.1em]">
                        {row.result}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-[12.5px] text-[#EEE9DF]/50">None.</p>
              )}
            </div>
          </div>
        </details>
      )}
    </div>
  );
}

/** Safe renderer for older saved reports that stored the V1 factor list. */
function LegacyReport({ report }: { report: Report }) {
  return (
    <div className="mt-6">
      <p className="text-center font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
        {report.label}
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {report.factors?.map((factor, index) => (
          <div key={index} className="rounded-lg border border-[#A62A34]/20 bg-[#160A0C]/60 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[13px] font-medium text-[#F7F5F0]">{factor.label}</div>
                <div className="mt-0.5 text-[12px] text-[#EEE9DF]/55">{factor.subtitle}</div>
              </div>
              <span
                className={`shrink-0 rounded border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em] ${
                  STATUS_STYLE[factor.status] ?? STATUS_STYLE.Mixed
                }`}
              >
                {factor.status}
              </span>
            </div>
            <p className="mt-2 text-[12.5px] leading-relaxed text-[#EEE9DF]/75">{factor.summary}</p>
          </div>
        ))}
      </div>
      {report.summary && (
        <p className="mt-5 text-[14px] leading-relaxed text-[#EEE9DF]/80">{report.summary}</p>
      )}
    </div>
  );
}

const SECTION = 'font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]';

function ProfileCard({
  title,
  profile,
  onChange,
}: {
  title: string;
  profile: Profile;
  onChange: (next: Profile) => void;
}) {
  const [query, setQuery] = useState(profile.place);
  const [hits, setHits] = useState<Array<{ id: string; name: string; region: string; country: string; coordinates: { lat: number; lng: number }; timezone?: string | null }>>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 3 || trimmed === profile.place) {
      setHits([]);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const outcome = await api.searchPlacesDetailed(trimmed);
        if (!cancelled) setHits(outcome.results);
      } catch {
        if (!cancelled) setHits([]);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 450);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query, profile.place]);

  const pick = (hit: (typeof hits)[number]) => {
    const label = [hit.name, hit.region, hit.country].filter(Boolean).join(', ');
    onChange({
      ...profile,
      place: label,
      lat: hit.coordinates.lat,
      lon: hit.coordinates.lng,
      tz: hit.timezone ?? undefined,
    });
    setQuery(label);
    setHits([]);
  };

  return (
    <section className={PANEL}>
      <div className="flex items-center justify-between">
        <div className={LABEL}>{title}</div>
        <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[#EEE9DF]/35">
          Traditional role
        </span>
      </div>
      <div className="mt-4 space-y-3">
        <div>
          <label className={LABEL} htmlFor={`${title}-name`}>Name</label>
          <input
            id={`${title}-name`}
            className={FIELD}
            value={profile.name}
            placeholder="Enter person's name"
            onChange={(e) => onChange({ ...profile, name: e.target.value })}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className={LABEL} htmlFor={`${title}-date`}>Date of birth</label>
            <input id={`${title}-date`} type="date" className={FIELD} value={profile.date}
                   onChange={(e) => onChange({ ...profile, date: e.target.value })} />
          </div>
          <div>
            <label className={LABEL} htmlFor={`${title}-time`}>Time of birth</label>
            <input id={`${title}-time`} type="time" className={FIELD} value={profile.time}
                   onChange={(e) => onChange({ ...profile, time: e.target.value })} />
          </div>
        </div>
        <div>
          <label className={LABEL} htmlFor={`${title}-place`}>Birth place</label>
          <input
            id={`${title}-place`}
            className={FIELD}
            value={query}
            placeholder="Search a city"
            autoComplete="off"
            onChange={(e) => { setQuery(e.target.value); onChange({ ...profile, place: '', lat: undefined, lon: undefined, tz: undefined }); }}
          />
          {searching && <p className="mt-1 text-[11px] text-[#EEE9DF]/40">Searching…</p>}
          {hits.length > 0 && (
            <ul className="mt-1 overflow-hidden rounded border border-[#A62A34]/30 bg-[#0E0708]">
              {hits.map((hit) => (
                <li key={hit.id}>
                  <button
                    type="button"
                    onClick={() => pick(hit)}
                    className="block w-full px-3 py-2 text-left text-[13px] text-[#EEE9DF]/80 hover:bg-[#2B0C11]/60"
                  >
                    {[hit.name, hit.region, hit.country].filter(Boolean).join(', ')}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {profile.place && (
            <p className="mt-1 text-[11px] text-[#EEE9DF]/40">Selected: {profile.place}</p>
          )}
        </div>
      </div>
    </section>
  );
}
