'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { SectionLabel } from '../../components/SectionLabel';
import { Kundli } from '../../components/Kundli';
import { BirthDetailsFlow } from '../../components/BirthDetails';
import { RetrogradePlanets } from '../../components/RetrogradePlanets';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import type { BirthDetails as BirthDetailsType } from '../../lib/types';
import { BnnConnections } from '../../components/kundli/BnnConnections';
import { ChartAnalysis } from '../../components/kundli/ChartAnalysis';
import { KundliCharts } from '../../components/kundli/KundliCharts';
import { StrengthEvidence } from '../../components/kundli/StrengthEvidence';
import {
  birthDetailsFor,
  fetchKundli,
  fetchKundliTransits,
  toKundliData,
  type KundliResponse,
  type KundliTransitResponse,
} from '../../lib/kundli';
import { useAuth } from '../../lib/auth';
import { getReading, saveKundliReading } from '../../lib/history';
import { loginHref } from '../../lib/authPaths';

const TABS = ['OVERVIEW', 'CHARTS', 'PLANETS', 'NAKSHATRAS', 'PANCHANG',
  'BNN', 'STRENGTH', 'ANALYSIS', 'DASHA', 'TRANSITS'] as const;
type Tab = (typeof TABS)[number];

const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5';
const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const CELL = 'px-3 py-2 text-left text-[12.5px] whitespace-nowrap';

function degree(value: number): string {
  const whole = Math.floor(value);
  const minutes = Math.round((value - whole) * 60);
  return `${whole}° ${String(minutes).padStart(2, '0')}'`;
}

function stamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${String(date.getDate()).padStart(2, '0')} ${date.toLocaleString('en-GB', { month: 'short' })} ${date.getFullYear()}`;
}

function Table({ head, rows }: { head: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[560px] border-collapse">
        <thead>
          <tr>{head.map((label) => <th key={label} className={`${LABEL} border-b border-[#A62A34]/25 pb-2 ${CELL}`}>{label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className={index % 2 ? 'bg-[#0E0708]/40' : ''}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className={`${CELL} border-b border-[#A62A34]/10 text-[#EEE9DF]/85`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function KundliPage() {
  const [pending, setPending] = useState<BirthDetailsType | null>(null);
  const [kundli, setKundli] = useState<KundliResponse | null>(null);
  const [transits, setTransits] = useState<KundliTransitResponse | null>(null);
  const [transitError, setTransitError] = useState('');
  const [transitLoading, setTransitLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('OVERVIEW');
  const { status: authStatus, user } = useAuth();
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [saveError, setSaveError] = useState('');
  const [snapshotId, setSnapshotId] = useState<string | null>(null);
  const [snapshotNotice, setSnapshotNotice] = useState('');
  // One automatic save per generated result (guards rerenders, Strict Mode and
  // the OAuth resume path from inserting duplicates).
  const savedSignatureRef = useRef<string | null>(null);
  // Latest-request-wins across every async path that applies a chart (a fresh
  // generate, its transits, or a saved-snapshot load).
  const loadIdRef = useRef(0);

  const birthPayload = (details: BirthDetailsType) => ({
    name: (details as BirthDetailsType & { name?: string }).name ?? '',
    date: details.date,
    time: details.time,
    place: details.place,
    latitude: Number(details.latitude),
    longitude: Number(details.longitude),
    timezone: details.timezone || 'Asia/Kolkata',
  });

  // After an authenticated generation succeeds, keep it in My KAVACH.
  const autoSave = async (natal: KundliResponse, details: BirthDetailsType) => {
    if (!user) return;
    const signature = JSON.stringify(birthPayload(details));
    if (savedSignatureRef.current === signature) return;
    savedSignatureRef.current = signature;
    setSaveError('');
    setSaveState('saving');
    try {
      const id = await saveKundliReading(user.id, birthPayload(details), natal);
      setSnapshotId(id);
      setSaveState('saved');
    } catch (exc) {
      savedSignatureRef.current = null; // a failed save may be retried
      setSaveState('idle');
      setSaveError(exc instanceof Error ? exc.message : 'We could not save this Kundli. Please try again.');
    }
  };

  const loadTransits = async (payload: ReturnType<typeof birthPayload>, loadId: number) => {
    setTransitLoading(true);
    setTransitError('');
    try {
      const transitData = await fetchKundliTransits(payload);
      if (loadId !== loadIdRef.current) return;
      setTransits(transitData);
    } catch {
      if (loadId !== loadIdRef.current) return;
      setTransitError('Transit data couldn\'t be loaded.');
    } finally {
      if (loadId === loadIdRef.current) setTransitLoading(false);
    }
  };

  const generate = async (details: BirthDetailsType) => {
    // The chart is public: a guest calculates immediately. Saving to My KAVACH
    // is the only account-gated step, and it never runs for a guest (see
    // autoSave, which requires a signed-in user).
    setPending(details);
    setBusy(true);
    setError('');
    setTransitError('');
    setTransitLoading(false);
    setKundli(null);
    setTransits(null);
    setSaveState('idle');
    setSaveError('');
    setSnapshotId(null);
    setSnapshotNotice('');
    savedSignatureRef.current = null;
    const loadId = loadIdRef.current + 1;
    loadIdRef.current = loadId;

    const payload = birthPayload(details);

    try {
      const natal = await fetchKundli(payload);
      if (loadId !== loadIdRef.current) return;
      setKundli(natal);
      setTab('OVERVIEW');
      void autoSave(natal, details);
    } catch (exc) {
      if (loadId !== loadIdRef.current) return;
      setError(exc instanceof Error ? exc.message : 'We could not generate this Kundli. Please try again.');
      setBusy(false);
      return;
    }

    // Transits are secondary: a failure must never discard the natal Kundli.
    await loadTransits(payload, loadId);
    if (loadId === loadIdRef.current) setBusy(false);
  };

  const retryTransits = () => {
    if (!pending) return;
    const loadId = loadIdRef.current + 1;
    loadIdRef.current = loadId;
    void loadTransits(birthPayload(pending), loadId);
  };

  // A saved Kundli is re-opened from its stored snapshot, never recalculated.
  useEffect(() => {
    if (authStatus === 'loading') return;
    const savedId = new URLSearchParams(window.location.search).get('saved');
    if (!savedId) return;

    if (authStatus !== 'signedIn' || !user) {
      setSnapshotNotice('Sign in to open this saved Kundli.');
      return;
    }

    let active = true;
    const loadId = loadIdRef.current + 1;
    loadIdRef.current = loadId;
    (async () => {
      try {
        const reading = await getReading(user.id, savedId);
        if (!active || loadId !== loadIdRef.current) return;
        if (!reading || reading.type !== 'kundli' || !reading.result_data) {
          setSnapshotNotice('That saved Kundli could not be found.');
          return;
        }
        setKundli(reading.result_data as KundliResponse);
        setPending(reading.input_data as unknown as BirthDetailsType);
        setSnapshotId(reading.id);
        setTab('OVERVIEW');
        setSnapshotNotice('');
      } catch (exc) {
        if (!active || loadId !== loadIdRef.current) return;
        setSnapshotNotice(exc instanceof Error ? exc.message : 'We could not open that saved Kundli.');
      }
    })();

    return () => {
      active = false;
    };
  }, [authStatus, user]);

  const saveToHistory = async () => {
    if (!kundli || !pending) return;
    if (!user) {
      window.location.href = loginHref('/kundli');
      return;
    }
    setSaveError('');
    setSaveState('saving');
    try {
      const id = await saveKundliReading(user.id, birthPayload(pending), kundli);
      setSnapshotId(id);
      setSaveState('saved');
    } catch (exc) {
      setSaveState('idle');
      setSaveError(exc instanceof Error ? exc.message : 'We could not save this Kundli. Please try again.');
    }
  };

  const reset = () => {
    setKundli(null);
    setTransits(null);
    setTransitLoading(false);
    setPending(null);
    setError('');
    setTransitError('');
    setSaveState('idle');
    setSaveError('');
    setSnapshotId(null);
    setSnapshotNotice('');
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-8 sm:py-12">
        <MaskedReveal>
          <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">
            KAVACH <span className="text-[#A62A34]">&bull;</span> Vedic Chart Tools
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">KUNDLI GENERATOR</h1>
          <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-[#EEE9DF]/50">
            Generate your sidereal birth chart and explore planetary positions, Nakshatras, birth Panchang,
            Dashas and current transits.
          </p>
        </MaskedReveal>

        {!kundli && (
          <section className={`${PANEL} mt-6`}>
            <SectionLabel label="Birth Details" number="01" tone="crimson" />
            <div className="mt-4">
              <BirthDetailsFlow
                onComplete={generate}
                onCancel={() => setPending(null)}
                initialDetails={pending ?? undefined}
                showName
                requireName
              />
            </div>
            {busy && (
              <div className="mt-5 border-t border-[#A62A34]/20 pt-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#B39250]">Calculating your Kundli</div>
                <p className="mt-1 text-[13px] text-[#EEE9DF]/55">
                  Calculating planetary positions, Panchang and Vimshottari periods&hellip;
                </p>
              </div>
            )}
            {error && (
              <div className="mt-4 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
                {error}
              </div>
            )}
          </section>
        )}

        {kundli && (
          <>
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <SectionLabel label="Kundli" number="02" tone="crimson" />
                {snapshotId && (
                  <span className="rounded border border-[#B39250]/40 bg-[#B39250]/10 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] text-[#D6BE85]">
                    Saved snapshot
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4">
                {!snapshotId && (
                  <button
                    onClick={() => void saveToHistory()}
                    disabled={saveState === 'saving'}
                    className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#D6BE85] transition-colors hover:text-[#F7F5F0] disabled:opacity-50"
                  >
                    {saveState === 'saving' ? 'Saving…' : 'Save to history'}
                  </button>
                )}
                <button onClick={reset} className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#EEE9DF]/50 hover:text-[#D6BE85]">
                  New Kundli
                </button>
              </div>
            </div>

            {saveError && (
              <div role="alert" className="mt-3 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12.5px] text-[#EEE9DF]/80">
                {saveError}
              </div>
            )}
            {snapshotNotice && (
              <div className="mt-3 flex flex-wrap items-center gap-3 rounded border border-[#A62A34]/30 bg-[#160A0C]/60 p-3 text-[12.5px] text-[#EEE9DF]/75">
                <span>{snapshotNotice}</span>
                {authStatus !== 'signedIn' && (
                  <a
                    href={loginHref('/kundli')}
                    className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#D6BE85] hover:text-[#F7F5F0]"
                  >
                    Sign in
                  </a>
                )}
              </div>
            )}

            <div className="mt-3 -mx-1 overflow-x-auto px-1">
              <div className="flex min-w-max gap-1.5 border-b border-[#A62A34]/25 pb-2">
                {TABS.map((item) => (
                  <button
                    key={item}
                    onClick={() => setTab(item)}
                    aria-selected={tab === item}
                    className={`rounded px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                      tab === item
                        ? 'bg-[#7B1D26] text-[#F7F5F0]'
                        : 'text-[#EEE9DF]/50 hover:text-[#D6BE85]'
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            {tab === 'OVERVIEW' && (
              <section className={`${PANEL} mt-4`}>
                <div className={LABEL}>Birth</div>
                <div className="mt-1 text-lg font-semibold text-[#F7F5F0]">{kundli.birth.name || 'Unnamed native'}</div>
                <div className="mt-1 text-[13px] text-[#EEE9DF]/60">
                  {kundli.birth.date} &middot; {kundli.birth.time} &middot; {kundli.birth.place}
                </div>
                <div className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-3">
                  {[
                    ['Lagna', kundli.summary.lagna],
                    ['Moon Rashi', kundli.summary.moonRashi],
                    ['Sun Rashi', kundli.summary.sunRashi],
                    ['Birth Nakshatra', `${kundli.summary.nakshatra} · pada ${kundli.summary.pada}`],
                    ['Paksha', kundli.summary.paksha],
                    ['Tithi', kundli.summary.tithi],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <div className={LABEL}>{label}</div>
                      <div className="mt-1 text-[14px] text-[#F7F5F0]">{value}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {tab === 'OVERVIEW' && (
              <RetrogradePlanets planets={kundli.planets} className="mt-4" />
            )}

            {tab === 'CHARTS' && (
              <div className="mt-4">
                <KundliCharts data={kundli} />
              </div>
            )}

            {tab === 'PLANETS' && (
              <section className={`${PANEL} mt-4`}>
                <div className={LABEL}>Planetary Positions</div>
                <div className="mt-3">
                  <Table
                    head={['Planet', 'Rashi', 'Degree', 'House', 'Nakshatra', 'Pada', 'Lord', 'Motion']}
                    rows={kundli.planets.map((planet) => [
                      <span key="p" className="font-semibold text-[#F7F5F0]">{planet.planet}</span>,
                      planet.rashi,
                      degree(planet.degree),
                      planet.house,
                      planet.nakshatra,
                      planet.pada,
                      planet.nakshatraLord,
                      planet.motion,
                    ])}
                  />
                </div>
              </section>
            )}

            {tab === 'NAKSHATRAS' && (
              <section className={`${PANEL} mt-4`}>
                <div className={LABEL}>Birth Nakshatra</div>
                <div className="mt-2 grid gap-x-6 gap-y-3 sm:grid-cols-3">
                  <div>
                    <div className={LABEL}>Name</div>
                    <div className="mt-1 text-[15px] text-[#F7F5F0]">{kundli.dasha.birthNakshatra}</div>
                  </div>
                  <div>
                    <div className={LABEL}>Pada</div>
                    <div className="mt-1 text-[15px] text-[#F7F5F0]">{kundli.summary.pada}</div>
                  </div>
                  <div>
                    <div className={LABEL}>Lord</div>
                    <div className="mt-1 text-[15px] text-[#F7F5F0]">{kundli.dasha.birthNakshatraLord}</div>
                  </div>
                </div>
                <div className={`${LABEL} mt-5`}>Planetary Nakshatras</div>
                <div className="mt-3">
                  <Table
                    head={['Planet', 'Nakshatra', 'Pada', 'Lord']}
                    rows={kundli.planets.map((planet) => [
                      <span key="p" className="font-semibold text-[#F7F5F0]">{planet.planet}</span>,
                      planet.nakshatra,
                      planet.pada,
                      planet.nakshatraLord,
                    ])}
                  />
                </div>
                <div className={`${LABEL} mt-5`}>Ascendant Nakshatra</div>
                <div className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-4">
                  {[
                    ['Lagna', kundli.chart.ascendant.rashi],
                    ['Nakshatra', kundli.chart.ascendant.nakshatra || kundli.summary.ascendantNakshatra],
                    ['Pada', kundli.chart.ascendant.pada || kundli.summary.ascendantPada],
                    ['Lord', kundli.chart.ascendant.nakshatraLord || kundli.summary.ascendantNakshatraLord],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <div className={LABEL}>{label}</div>
                      <div className="mt-1 text-[15px] text-[#F7F5F0]">{value || '—'}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {tab === 'BNN' && (
              <div className="mt-4">
                <BnnConnections data={kundli} />
              </div>
            )}

            {tab === 'STRENGTH' && (
              <div className="mt-4">
                <StrengthEvidence data={kundli} />
              </div>
            )}

            {tab === 'ANALYSIS' && (
              <div className="mt-4">
                <ChartAnalysis data={kundli} />
              </div>
            )}

            {tab === 'DASHA' && (
              <section className="mt-4 space-y-4">
                <div className={PANEL}>
                  <div className={LABEL}>Current Period</div>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">
                    {kundli.dasha.currentMahadasha && (
                      <div className="rounded border border-[#A62A34]/30 bg-[#0E0708]/50 p-3">
                        <div className={LABEL}>Mahadasha</div>
                        <div className="mt-1 text-lg font-semibold text-[#F7F5F0]">{kundli.dasha.currentMahadasha.lord}</div>
                        <div className="mt-1 text-[12.5px] text-[#EEE9DF]/60">
                          {stamp(kundli.dasha.currentMahadasha.start)} &rarr; {stamp(kundli.dasha.currentMahadasha.end)}
                        </div>
                      </div>
                    )}
                    {kundli.dasha.currentAntardasha && (
                      <div className="rounded border border-[#A62A34]/30 bg-[#0E0708]/50 p-3">
                        <div className={LABEL}>Antardasha</div>
                        <div className="mt-1 text-lg font-semibold text-[#F7F5F0]">{kundli.dasha.currentAntardasha.lord}</div>
                        <div className="mt-1 text-[12.5px] text-[#EEE9DF]/60">
                          {stamp(kundli.dasha.currentAntardasha.start)} &rarr; {stamp(kundli.dasha.currentAntardasha.end)}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 text-[12.5px] text-[#EEE9DF]/50">
                    Birth balance: {kundli.dasha.balanceAtBirth.lord} &middot; {kundli.dasha.balanceAtBirth.years.toFixed(2)} years remaining
                    at birth (progress {(kundli.dasha.progressAtBirth * 100).toFixed(1)}% through {kundli.dasha.birthNakshatra})
                  </div>
                </div>

                <div className={PANEL}>
                  <div className={LABEL}>Vimshottari Mahadasha</div>
                  <div className="mt-3">
                    <Table
                      head={['Lord', 'Start', 'End', 'Years']}
                      rows={kundli.dasha.mahadashas.map((period) => {
                        const current = kundli.dasha.currentMahadasha?.start === period.start;
                        return [
                          <span key="l" className={current ? 'font-semibold text-[#D6BE85]' : 'text-[#F7F5F0]'}>
                            {period.lord}{current ? ' · current' : ''}
                          </span>,
                          stamp(period.start),
                          stamp(period.end),
                          period.years.toFixed(2),
                        ];
                      })}
                    />
                  </div>
                </div>
              </section>
            )}

            {tab === 'TRANSITS' && (
              <section className={`${PANEL} mt-4`}>
                <div className={LABEL}>Current Transits</div>
                {transitLoading ? (
                  <div className="mt-3 text-[13px] text-[#EEE9DF]/60" role="status">Loading transit data&hellip;</div>
                ) : transitError ? (
                  <div className="mt-3 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
                    <div>Transit data couldn&apos;t be loaded. The natal Kundli above is unaffected.</div>
                    <button
                      type="button"
                      onClick={retryTransits}
                      className="mt-3 rounded border border-[#D6BE85]/50 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-[#D6BE85] hover:border-[#D6BE85]"
                    >
                      Retry
                    </button>
                  </div>
                ) : transits ? (
                  <>
                    <div className="mt-2 rounded border border-[#A62A34]/30 bg-[#0E0708]/50 px-3 py-2">
                      <span className={LABEL}>As of</span>{' '}
                      <span className="text-[13px] text-[#F7F5F0]">
                        {transits.asOf.timestamp.slice(0, 10)} &middot; {transits.asOf.timestamp.slice(11, 16)} &middot; {transits.asOf.timezone}
                      </span>
                    </div>
                    <div className="mt-3">
                      <Table
                        head={['Planet', 'Current Rashi', 'Degree', 'Nakshatra', 'Pada', 'Natal House']}
                        rows={transits.transits.map((row) => [
                          <span key="p" className="font-semibold text-[#F7F5F0]">{row.planet}</span>,
                          row.rashi,
                          degree(row.degree),
                          row.nakshatra,
                          row.pada,
                          row.natalHouse,
                        ])}
                      />
                    </div>
                  </>
                ) : (
                  <div className="mt-3 text-[13px] text-[#EEE9DF]/50">Transits were not calculated.</div>
                )}
              </section>
            )}

            {tab === 'PANCHANG' && (
              <section className={`${PANEL} mt-4`}>
                <div className={LABEL}>Birth Panchang</div>
                <div className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-3">
                  {[
                    ['Vara', kundli.panchang.vara],
                    ['Tithi', kundli.panchang.tithi],
                    ['Paksha', kundli.panchang.paksha],
                    ['Nakshatra', kundli.panchang.nakshatra],
                    ['Pada', kundli.panchang.pada],
                    ['Yoga', kundli.panchang.yoga],
                    ['Karana', kundli.panchang.karana],
                    ['Sun Rashi', kundli.panchang.sunRashi],
                    ['Moon Rashi', kundli.panchang.moonRashi],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <div className={LABEL}>{label}</div>
                      <div className="mt-1 text-[14px] text-[#F7F5F0]">{value}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </Container>
    </main>
  );
}
