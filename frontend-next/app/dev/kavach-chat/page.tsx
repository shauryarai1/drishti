'use client';

import React, { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../../../lib/api';

interface City { label: string; latitude: number; longitude: number; timezone: string }

const CITIES: City[] = [
  { label: 'New Delhi', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' },
  { label: 'Mumbai', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { label: 'Bengaluru', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  { label: 'London', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { label: 'New York', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { label: 'Dubai', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { label: 'Sydney', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
];

interface Turn {
  id: number;
  question: string;
  usedTimestamp: string;
  status: string;
  answer: string | null;
  channels?: unknown;
  classification?: unknown;
  prashna?: unknown;
  synthesis?: unknown;
  rulesMatched: string[];
  moment: Record<string, never> | null;
  isFollowUp: boolean;
}

const withOffset = (d: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? '+' : '-';
  const abs = Math.abs(off);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
};

const pretty = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', second: '2-digit' });
};

export default function KavachChatDev() {
  const [city, setCity] = useState<City>(CITIES[0]);
  const [override, setOverride] = useState(false);
  const [overrideDate, setOverrideDate] = useState(new Date().toISOString().slice(0, 10));
  const [overrideTime, setOverrideTime] = useState('14:15');
  const [followUp, setFollowUp] = useState(true);
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [clock, setClock] = useState(new Date());
  const [busy, setBusy] = useState(false);
  const nextId = useRef(1);

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const send = async () => {
    const question = input.trim();
    if (!question || busy) return;
    setBusy(true);
    setInput('');

    const now = new Date();
    const timestamp = override
      ? (() => {
          const local = new Date(`${overrideDate}T${overrideTime}:00`);
          return withOffset(local);
        })()
      : withOffset(now);

    const previous = turns.find((t) => t.status !== 'error');
    const body = {
      question,
      timestamp,
      latitude: city.latitude,
      longitude: city.longitude,
      timezone: city.timezone,
      location_label: city.label,
      is_follow_up: Boolean(previous) && followUp,
      original_timestamp: previous?.usedTimestamp ?? null,
    };

    try {
      const res = await fetch(`${API_BASE}/dev/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setTurns((prev) => [
        ...prev,
        {
          id: nextId.current++,
          question,
          usedTimestamp: data.used_timestamp ?? timestamp,
          status: data.status ?? 'error',
          answer: data.answer ?? data.message ?? null,
          rulesMatched: data.rules_matched ?? [],
          moment: data.context?.moment ?? null,
          channels: data.channels ?? null,
          classification: data.classification ?? null,
          prashna: data.prashna ?? null,
          synthesis: data.synthesis ?? null,
          isFollowUp: Boolean(data.is_follow_up),
        },
      ]);
    } catch {
      setTurns((prev) => [
        ...prev,
        { id: nextId.current++, question, usedTimestamp: timestamp, status: 'error', answer: 'Request failed.', rulesMatched: [], moment: null, isFollowUp: false },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const box = 'rounded border border-[#A62A34]/35 bg-[#160A0C] px-3 py-2 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <div className="mx-auto w-full max-w-4xl px-5 py-8">
        <div className="border-b border-[#A62A34]/25 pb-3">
          <div className="font-bold tracking-[0.28em] text-[#F7F5F0]">KAVACH</div>
          <div className="text-xs uppercase tracking-[0.2em] text-[#B39250]">Question Chat · System B</div>
          <div className="mt-1 font-mono text-[10px] text-[#E53E3E]">
            LOCAL TESTING ONLY · NO BIRTH DETAILS · EXACT QUESTION MOMENT
          </div>
        </div>

        {/* Controls */}
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Location</span>
            <select className={box} value={city.label} onChange={(e) => setCity(CITIES.find((c) => c.label === e.target.value) || CITIES[0])}>
              {CITIES.map((c) => <option key={c.label} value={c.label}>{c.label} · {c.timezone}</option>)}
            </select>
          </label>

          <div className="flex flex-col gap-1">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Current question moment</span>
            <span className="font-mono text-sm text-[#F7F5F0]">{pretty(withOffset(clock))}</span>
          </div>

          <label className="flex items-center gap-2 pb-2 text-xs text-[#EEE9DF]/70">
            <input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} />
            Override question time
          </label>

          {override && (
            <>
              <input type="date" className={box} value={overrideDate} onChange={(e) => setOverrideDate(e.target.value)} />
              <input type="time" step={1} className={box} value={overrideTime} onChange={(e) => setOverrideTime(e.target.value)} />
              <span className="pb-2 font-mono text-[10px] text-[#E53E3E]">TEST ONLY</span>
            </>
          )}

          <label className="flex items-center gap-2 pb-2 text-xs text-[#EEE9DF]/70">
            <input type="checkbox" checked={followUp} onChange={(e) => setFollowUp(e.target.checked)} />
            Follow-up (keep previous moment)
          </label>
        </div>

        {/* Chat */}
        <div className="mt-5 space-y-3">
          {turns.map((turn) => (
            <div key={turn.id} className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4">
              <div className="text-xs uppercase tracking-[0.16em] text-[#B39250]">You</div>
              <div className="mt-1 text-[15px] text-[#F7F5F0]">{turn.question}</div>

              <div className="mt-3 border-t border-[#A62A34]/20 pt-3">
                <div className="text-xs uppercase tracking-[0.16em] text-[#B39250]">KAVACH</div>
                {turn.status === 'no_approved_rule' && (
                  <div className="mt-2 rounded border border-[#B39250]/30 bg-[#090909]/60 p-3 text-sm text-[#EEE9DF]/85">
                    {turn.answer}
                  </div>
                )}
                {turn.status === 'rule_matched' && (
                  <div className="mt-2 text-sm text-[#F7F5F0]">{turn.answer ?? 'Rule matched.'}</div>
                )}
                {turn.status === 'error' && (
                  <div className="mt-2 rounded border border-[#E53E3E]/50 bg-[#541219]/30 p-3 text-sm">{turn.answer}</div>
                )}
                <div className="mt-2 font-mono text-[10px] text-[#EEE9DF]/45">
                  moment used: {pretty(turn.usedTimestamp)} · {city.timezone} · {city.latitude}, {city.longitude}
                  {turn.isFollowUp ? ' · follow-up (original moment retained)' : ''}
                </div>
              </div>

              <details className="mt-3">
                <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-[#D6BE85]">Calculation debug</summary>
                {turn.moment ? (
                  <pre className="mt-2 max-h-80 overflow-auto rounded border border-[#A62A34]/25 bg-[#090909] p-3 font-mono text-[11px] text-[#EEE9DF]/85">
{JSON.stringify({ moment: turn.moment, classification: turn.classification, placementReadings: turn.channels, synthesis: turn.synthesis, prashna: turn.prashna }, null, 2)}
                  </pre>
                ) : <div className="mt-2 text-xs text-[#EEE9DF]/50">No moment context.</div>}
              </details>
            </div>
          ))}
        </div>

        {/* Composer */}
        <div className="sticky bottom-0 mt-5 flex gap-2 bg-[#090909]/95 py-3 backdrop-blur">
          <input
            className={`${box} flex-1`}
            placeholder="Ask KAVACH…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <button
            onClick={send}
            disabled={busy}
            className="rounded bg-[#7B1D26] px-5 py-2 text-sm font-semibold text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50"
          >
            {busy ? '…' : 'Send'}
          </button>
        </div>

        <p className="mt-2 text-[11px] text-[#EEE9DF]/45">
          Birth details are never requested or used here. The calculation uses the exact moment the question is sent and the selected location.
        </p>
      </div>
    </main>
  );
}
