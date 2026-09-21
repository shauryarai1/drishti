'use client';

import React, { useState } from 'react';
import { API_BASE } from '../../lib/api';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { Header } from '../../components/Header';
import { CurrentDashaSection } from '../../components/CurrentDashaSection';

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
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [place, setPlace] = useState('');
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<Array<{ display: string; lat: number; lon: number }>>([]);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const search = async () => {
    if (query.trim().length < 3) return;
    try {
      const res = await fetch(`${API_BASE}/places/search?q=${encodeURIComponent(query.trim())}`);
      const body = await res.json();
      setHits(body.results || []);
    } catch {
      setHits([]);
    }
  };

  const submit = async () => {
    if (!date || !time || !place.trim()) return;
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/life-summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          time,
          place,
          latitude: coords?.lat ?? null,
          longitude: coords?.lon ?? null,
          timezone: 'Asia/Kolkata',
        }),
      });
      const body = await res.json();
      if (body.status === 'error') throw new Error(body.message);
      setSummary(body);
    } catch {
      setError("We couldn't prepare your life summary right now. Please try again.");
    } finally {
      setBusy(false);
    }
  };

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
                <button onClick={search} className="rounded border border-[#A62A34]/35 px-4 py-3 text-xs uppercase tracking-wide text-[#EEE9DF]/80 hover:text-[#F7F5F0]">
                  Search
                </button>
              </div>
              {hits.length > 0 && (
                <div className="rounded border border-[#A62A34]/25">
                  {hits.map((h, i) => (
                    <div
                      key={i}
                      onClick={() => { setPlace(h.display); setCoords({ lat: h.lat, lon: h.lon }); setHits([]); setQuery(h.display); }}
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

        {summary && (
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
