'use client';

import React, { useState } from 'react';
import { API_BASE } from '../lib/api';
import { searchWeeklyPlaces, type WeeklyPlace } from '../lib/weekly';

// CURRENT DASHA - premium product card shown on the Life Summary page.
// Birth details resolve through the same KAVACH place autocomplete used by
// /your-week, and the reading comes only from the customer-safe endpoint.

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const FIELD = 'mt-1 w-full rounded border border-[#A62A34]/35 bg-[#0E0708] px-3 py-2.5 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';

interface CurrentDashaReading {
  asOf: string;
  timezone: string;
  mahadasha: { name: string; start: string; end: string };
  antardasha: { name: string; start: string; end: string };
  headline: string;
  summary: string;
  supports: string[];
  care: string[];
  guidance: string;
}

function range(startIso: string, endIso: string): string {
  const year = (iso: string) => (iso ? iso.slice(0, 4) : '');
  return `${year(startIso)} — ${year(endIso)}`;
}

function PlaceInput({ label, value, onResolve }: {
  label: string; value: WeeklyPlace | null; onResolve: (place: WeeklyPlace | null, raw: string) => void;
}) {
  const [text, setText] = useState(value?.label ?? '');
  const [options, setOptions] = useState<WeeklyPlace[]>([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  React.useEffect(() => {
    if (value) return;
    const trimmed = text.trim();
    if (trimmed.length < 3) { setOptions([]); setOpen(false); return; }
    let cancelled = false;
    setBusy(true);
    const timer = setTimeout(async () => {
      const found = await searchWeeklyPlaces(trimmed);
      if (cancelled) return;
      setOptions(found);
      setOpen(found.length > 0);
      setBusy(false);
    }, 250);
    return () => { cancelled = true; clearTimeout(timer); setBusy(false); };
  }, [text, value]);

  const choose = (place: WeeklyPlace) => {
    onResolve(place, place.label);
    setText(place.label);
    setOptions([]);
    setOpen(false);
  };

  return (
    <label className="relative block">
      <span className={LABEL}>{label}</span>
      <input
        className={FIELD}
        value={text}
        autoComplete="off"
        placeholder="Search place"
        onChange={(event) => {
          setText(event.target.value);
          if (value && event.target.value !== value.label) onResolve(null, event.target.value);
          setOpen(false);
        }}
        onFocus={() => { if (options.length > 0) setOpen(true); }}
        onBlur={() => setTimeout(() => setOpen(false), 140)}
      />
      {busy && <span className="mt-1 block text-[11px] text-[#EEE9DF]/40">Searching&hellip;</span>}
      {value && (
        <span className="mt-1 block text-[11px] text-[#7BD88F]">
          {value.label} &middot; {value.latitude.toFixed(3)}, {value.longitude.toFixed(3)}
        </span>
      )}
      {open && options.length > 0 && (
        <ul className="absolute z-30 mt-1 max-h-56 w-full overflow-auto rounded border border-[#A62A34]/40 bg-[#160A0C] shadow-[0_20px_60px_rgba(0,0,0,0.85)]">
          {options.map((option, index) => (
            <li key={`${option.label}-${index}`}>
              <button
                type="button"
                onMouseDown={(event) => { event.preventDefault(); choose(option); }}
                className="block w-full px-3 py-2 text-left text-[12.5px] text-[#EEE9DF]/75 hover:bg-[#2B0C11] hover:text-[#F7F5F0]"
              >
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  );
}

export function CurrentDashaSection() {
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState('1990-05-15');
  const [time, setTime] = useState('14:15');
  const [place, setPlace] = useState<WeeklyPlace | null>(null);
  const [reading, setReading] = useState<CurrentDashaReading | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const generate = async () => {
    if (!place) { setError('Please select a valid birth place.'); return; }
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/current-dasha-reading`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth: { date, time, place: place.label, latitude: place.latitude,
                   longitude: place.longitude, timezone: place.timezone },
        }),
      });
      const body = await res.json();
      if (!res.ok || body.status === 'error') throw new Error(body.message || 'unavailable');
      setReading(body as CurrentDashaReading);
    } catch {
      setError("We couldn't prepare the current dasha reading with those details.");
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <section className="mt-6 rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70 p-6">
        <div className="flex items-center gap-3">
          <span className="rounded border border-[#B39250]/40 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.2em] text-[#B39250]">
            Premium
          </span>
          <span className={LABEL}>Life Summary</span>
        </div>
        <h2 className="mt-3 text-lg font-semibold tracking-[0.06em] text-[#F7F5F0]">CURRENT DASHA</h2>
        <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-[#EEE9DF]/55">
          Understand the larger phase you&apos;re moving through. See the main themes of your current
          Mahadasha, where the period may support you, and where a more careful approach may help.
        </p>
        <button
          onClick={() => setOpen(true)}
          className="mt-4 rounded bg-[#7B1D26] px-4 py-2.5 font-mono text-[10.5px] uppercase tracking-[0.16em] text-[#F7F5F0] hover:bg-[#A62A34]"
        >
          View My Current Dasha
        </button>
      </section>
    );
  }

  return (
    <section className="mt-6 rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="rounded border border-[#B39250]/40 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.2em] text-[#B39250]">
            Premium
          </span>
          <span className={LABEL}>Current Dasha</span>
        </div>
        {reading && (
          <button onClick={() => { setReading(null); setOpen(false); }} className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/50 hover:text-[#D6BE85]">
            Close
          </button>
        )}
      </div>

      {!reading && (
        <>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className={LABEL}>Date of Birth</span>
              <input type="date" className={FIELD} value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label className="block">
              <span className={LABEL}>Exact Birth Time</span>
              <input type="time" className={FIELD} value={time} onChange={(e) => setTime(e.target.value)} />
            </label>
            <PlaceInput label="Birth Place" value={place} onResolve={setPlace} />
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={generate}
              disabled={busy}
              className="rounded bg-[#7B1D26] px-4 py-2.5 font-mono text-[10.5px] uppercase tracking-[0.16em] text-[#F7F5F0] hover:bg-[#A62A34] disabled:opacity-50"
            >
              {busy ? 'Preparing…' : 'View My Current Dasha'}
            </button>
            <span className="text-[11px] text-[#EEE9DF]/35">
              Your birth details are used to prepare this reading.
            </span>
          </div>
          {error && (
            <div className="mt-3 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">{error}</div>
          )}
        </>
      )}

      {reading && (
        <>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded border border-[#A62A34]/30 bg-[#0E0708]/50 p-4">
              <div className={LABEL}>Current Mahadasha</div>
              <div className="mt-1 text-xl font-semibold text-[#F7F5F0]">{reading.mahadasha.name}</div>
              <div className="mt-1 text-[12.5px] text-[#EEE9DF]/55">{range(reading.mahadasha.start, reading.mahadasha.end)}</div>
            </div>
            <div className="rounded border border-[#A62A34]/30 bg-[#0E0708]/50 p-4">
              <div className={LABEL}>Current Antardasha</div>
              <div className="mt-1 text-xl font-semibold text-[#F7F5F0]">{reading.antardasha.name}</div>
              <div className="mt-1 text-[12.5px] text-[#EEE9DF]/55">{range(reading.antardasha.start, reading.antardasha.end)}</div>
            </div>
          </div>

          <h3 className="mt-5 text-[10px] uppercase tracking-[0.2em] text-[#B39250]">Your Current Phase</h3>
          <div className="mt-2 text-lg font-semibold text-[#F7F5F0]">{reading.headline}</div>
          <p className="mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/75">{reading.summary}</p>

          {reading.supports.length > 0 && (
            <div className="mt-4">
              <div className={LABEL}>What Supports You</div>
              <ul className="mt-2 space-y-1.5">
                {reading.supports.map((item) => (
                  <li key={item} className="text-[13px] leading-relaxed text-[#EEE9DF]/75">&middot; {item}</li>
                ))}
              </ul>
            </div>
          )}

          {reading.care.length > 0 && (
            <div className="mt-4">
              <div className={LABEL}>What May Need Care</div>
              <ul className="mt-2 space-y-1.5">
                {reading.care.map((item) => (
                  <li key={item} className="text-[13px] leading-relaxed text-[#E5B567]/85">&middot; {item}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4">
            <div className={LABEL}>How to Work With This Period</div>
            <p className="mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/75">{reading.guidance}</p>
          </div>
        </>
      )}
    </section>
  );
}
