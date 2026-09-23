'use client';

import React, { useEffect, useRef, useState } from 'react';
import { API_BASE, api } from '../../lib/api';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { Header } from '../../components/Header';
import { CurrentDashaSection } from '../../components/CurrentDashaSection';
import { ResultGate } from '../../components/ResultGate';
import { useAuth } from '../../lib/auth';
import { loginHref } from '../../lib/authPaths';
import { savePendingForm, takePendingForm } from '../../lib/pendingForms';
import { authHeaders } from '../../lib/authHeaders';

interface Section {
  key: string;
  title: string;
  status: string;
  body: string | null;
  message?: string;
}
interface Summary {
  available_sections: number;
  total_sections: number;
  sections: Section[];
  note: string;
}

export default function LifeSummaryPage() {
  const { status: authStatus, user } = useAuth();
  const requestIdRef = useRef(0);
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [place, setPlace] = useState('');
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<Array<{ display: string; lat: number; lon: number; timezone: string | null }>>([]);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  // IANA timezone of the SELECTED place (from the backend). Null means unknown:
  // the backend then derives it from the coordinates, and we never assume
  // Asia/Kolkata for an arbitrary location.
  const [selectedTimezone, setSelectedTimezone] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchUnavailable, setSearchUnavailable] = useState(false);

  const search = async () => {
    const trimmed = query.trim();
    if (trimmed.length < 3) return;
    setSearching(true);
    setSearchUnavailable(false);
    try {
      // Shared hardened search: cached, deduped, and it tells us when the
      // location service is temporarily down (instead of "no cities").
      const outcome = await api.searchPlacesDetailed(trimmed);
      setHits(outcome.results.map((place) => ({
        display: `${place.name}${place.region ? `, ${place.region}` : ''}${place.country ? `, ${place.country}` : ''}`,
        lat: place.coordinates.lat,
        lon: place.coordinates.lng,
        timezone: place.timezone ?? null,
      })));
      setSearchUnavailable(outcome.unavailable);
    } catch {
      setHits([]);
      setSearchUnavailable(true);
    } finally {
      setSearching(false);
    }
  };

  const submit = async () => {
    if (!date || !time || !place.trim()) return;
    const payload = {
      date,
      time,
      place,
      latitude: coords?.lat ?? null,
      longitude: coords?.lon ?? null,
      // No hardcoded zone. Send the selected place's timezone when known;
      // otherwise omit it and the backend derives it from the coordinates.
      ...(selectedTimezone ? { timezone: selectedTimezone } : {}),
    };

    // The result is protected, not the form: preserve the details, sign in, resume.
    if (authStatus !== 'signedIn' || !user) {
      savePendingForm('life_summary', payload);
      window.location.href = loginHref('/life-summary');
      return;
    }

    await runSummary(payload);
  };

  const runSummary = async (payload: Record<string, unknown>) => {
    // Latest-request-wins: a superseded response must never overwrite the
    // current result, error or loading state.
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setBusy(true);
    setError('');
    try {
      // Verified identity for the archive: present only when signed in.
      const identity = await authHeaders();
      const res = await fetch(`${API_BASE}/life-summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...identity },
        body: JSON.stringify(payload),
      });
      const body = await res.json();
      if (body.status === 'error') throw new Error(body.message);
      if (requestId !== requestIdRef.current) return;
      setSummary(body);
    } catch {
      if (requestId !== requestIdRef.current) return;
      setError("We couldn't prepare your life summary right now. Please try again.");
    } finally {
      if (requestId === requestIdRef.current) setBusy(false);
    }
  };

  // Resume a pending life summary after the guest signs in.
  useEffect(() => {
    if (authStatus !== 'signedIn' || !user) return;
    const restored = takePendingForm('life_summary');
    if (!restored) return;
    setDate(restored.date);
    setTime(restored.time);
    setPlace(restored.place);
    if (typeof restored.latitude === 'number' && typeof restored.longitude === 'number') {
      setCoords({ lat: restored.latitude, lon: restored.longitude });
    }
    if (restored.timezone) setSelectedTimezone(restored.timezone);
    void runSummary({
      ...restored,
      latitude: restored.latitude ?? null,
      longitude: restored.longitude ?? null,
    });
    // The pending form is consumed on first use, so this cannot double-generate.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus, user]);

  const field = 'w-full rounded border border-[#A62A34]/35 bg-[#160A0C] px-3.5 py-3 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <div className="mx-auto w-full max-w-2xl px-5 pb-10 sm:pb-14">
        <MaskedReveal>
          <div>
            <div className="text-lg font-bold tracking-[0.28em] text-[#F7F5F0]">KAVACH</div>
            <h1 className="mt-1 text-2xl font-bold uppercase tracking-[0.16em] text-[#F7F5F0] sm:text-3xl">Your Life Summary</h1>
            <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/65">
              A summary of your life areas, prepared from your birth details.
            </p>
          </div>
        </MaskedReveal>

        {!summary && (
          <section className="mt-8 rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70 p-6">
            <h1 className="text-lg font-semibold text-[#F7F5F0]">Your birth details</h1>
            <p className="mt-1 text-sm text-[#EEE9DF]/60">We need these once to prepare your summary.</p>

            <div className="mt-5 space-y-3">
              <input type="date" className={field} value={date} onChange={(e) => setDate(e.target.value)} />
              <input type="time" className={field} value={time} onChange={(e) => setTime(e.target.value)} />

              <div className="flex gap-2">
                <input
                  className={field}
                  placeholder="Birth city"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && search()}
                />
                <button
                  onClick={search}
                  disabled={searching}
                  className="rounded border border-[#A62A34]/35 px-4 py-3 text-xs uppercase tracking-wide text-[#EEE9DF]/80 hover:text-[#F7F5F0] disabled:opacity-50"
                >
                  {searching ? 'Searching…' : 'Search'}
                </button>
              </div>
              {searchUnavailable && hits.length === 0 && (
                <p className="text-[11px] text-[#E5B567]">
                  Location search is temporarily unavailable. Please try again shortly.
                </p>
              )}
              {hits.length > 0 && (
                <div className="rounded border border-[#A62A34]/25">
                  {hits.map((h, i) => (
                    <div
                      key={i}
                      onClick={() => { setPlace(h.display); setCoords({ lat: h.lat, lon: h.lon }); setSelectedTimezone(h.timezone); setHits([]); setQuery(h.display); }}
                      className="cursor-pointer border-b border-[#A62A34]/15 px-3 py-2.5 text-sm last:border-0 hover:bg-[#2B0C11]"
                    >
                      {h.display}
                    </div>
                  ))}
                </div>
              )}
              {place && <div className="text-xs text-[#EEE9DF]/55">Selected: {place}</div>}

              <button
                onClick={submit}
                disabled={busy}
                className="mt-2 w-full rounded bg-[#7B1D26] px-4 py-3.5 text-sm font-semibold text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50"
              >
                {busy ? 'Preparing your summary…' : 'Prepare my summary'}
              </button>
            </div>

            {error && (
              <div className="mt-4 rounded border border-[#A62A34]/40 bg-[#541219]/30 p-3 text-sm">{error}</div>
            )}
          </section>
        )}

        {summary && authStatus === 'signedIn' && (
          <div className="mt-8 space-y-4">
            <div className="text-xs uppercase tracking-[0.2em] text-[#EEE9DF]/45">Your life summary</div>

            {summary.sections.map((section) => (
              <MaskedReveal key={section.key}>
                <section className="rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
                  <h2 className="text-lg font-semibold text-[#F7F5F0]">{section.title}</h2>
                  {section.status === 'available' && section.body ? (
                    <p className="mt-3 text-[15px] leading-relaxed text-[#EEE9DF]/80">{section.body}</p>
                  ) : (
                    <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/55">{section.message}</p>
                  )}
                </section>
              </MaskedReveal>
            ))}

            <button
              onClick={() => setSummary(null)}
              className="mt-2 text-xs uppercase tracking-wider text-[#D6BE85] hover:text-[#F7F5F0]"
            >
              ← Edit birth details
            </button>
          </div>
        )}
      </div>
            <CurrentDashaSection />
      </main>
  );
}
