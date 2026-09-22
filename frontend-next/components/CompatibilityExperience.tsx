'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { ResultGate } from './ResultGate';
import { API_BASE, api } from '../lib/api';
import { authHeaders } from '../lib/authHeaders';
import { useAuth } from '../lib/auth';
import { loginHref } from '../lib/authPaths';
import { isValidPersonName, normalisePersonName } from '../lib/personName';
import { savePendingForm, takePendingForm } from '../lib/pendingForms';
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
        throw new Error(body.message || "We couldn't prepare this compatibility report.");
      }
      setPeople(body.people as PersonView[]);
      setReport(body.report as Report);
      void autoSave(body.people as PersonView[], body.report as Report);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "We couldn't prepare this compatibility report.");
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
    if (authStatus !== 'signedIn' || !user) {
      savePendingForm('compatibility', {
        bride_name: normalisePersonName(bride.name), bride_date: bride.date, bride_time: bride.time,
        bride_place: bride.place, bride_latitude: bride.lat, bride_longitude: bride.lon, bride_timezone: bride.tz,
        groom_name: normalisePersonName(groom.name), groom_date: groom.date, groom_time: groom.time,
        groom_place: groom.place, groom_latitude: groom.lat, groom_longitude: groom.lon, groom_timezone: groom.tz,
      });
      window.location.href = loginHref('/compatibility');
      return;
    }
    submittingRef.current = true;
    await run(bride, groom);
  };

  // Resume a pending form after sign-in, or open a saved report from My KAVACH.
  useEffect(() => {
    if (authStatus !== 'signedIn' || !user) return;
    const params = new URLSearchParams(window.location.search);
    const savedId = params.get('saved');
    if (savedId) {
      (async () => {
        try {
          const reading = await getReading(user.id, savedId);
          const stored = reading?.result_data as { people?: PersonView[]; report?: Report } | undefined;
          if (reading?.type !== 'compatibility' || !stored?.report) {
            setError('That saved compatibility report could not be found.');
            return;
          }
          setPeople(stored.people ?? []);
          setReport(stored.report);
        } catch (exc) {
          setError(exc instanceof Error ? exc.message : 'We could not open that saved report.');
        }
      })();
      return;
    }
    const restored = takePendingForm('compatibility');
    if (!restored) return;
    const nextBride: Profile = {
      name: restored.bride_name ?? '', date: restored.bride_date ?? '', time: restored.bride_time ?? '',
      place: restored.bride_place ?? '', lat: restored.bride_latitude, lon: restored.bride_longitude,
      tz: restored.bride_timezone,
    };
    const nextGroom: Profile = {
      name: restored.groom_name ?? '', date: restored.groom_date ?? '', time: restored.groom_time ?? '',
      place: restored.groom_place ?? '', lat: restored.groom_latitude, lon: restored.groom_longitude,
      tz: restored.groom_timezone,
    };
    setBride(nextBride);
    setGroom(nextGroom);
    void run(nextBride, nextGroom);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus, user]);

  const ready = report !== null;

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="lg" className="py-10 sm:py-14">
        <SectionLabel label="KAVACH · Compatibility" tone="brass" />
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-4xl">
          MARRIAGE COMPATIBILITY
        </h1>
        <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-[#EEE9DF]/55">
          Traditional compatibility across the factors supported by the KAVACH method. Some rules are
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
              {busy ? 'Preparing…' : 'Check compatibility'}
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

        {authStatus === 'signedOut' && !ready && (
          <div className="mt-8">
            <ResultGate
              nextPath="/compatibility"
              title="SAVE & VIEW YOUR COMPATIBILITY REPORT"
              body="Sign in to view your compatibility report and keep it safely in My KAVACH."
            />
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
      <section className="rounded-xl border border-[#B39250]/30 bg-gradient-to-b from-[#2B0C11]/80 to-[#090909] p-6 text-center sm:p-8">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
          Overall assessment
        </div>
        <div className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">
          {report.overall?.state}
        </div>
        <p className="mx-auto mt-3 max-w-2xl text-[14px] leading-relaxed text-[#EEE9DF]/80">
          {report.overall?.summary}
        </p>
      </section>

      <section>
        <h3 className={SECTION}>Your compatibility at a glance</h3>
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
        <h3 className={SECTION}>In-depth compatibility</h3>
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
