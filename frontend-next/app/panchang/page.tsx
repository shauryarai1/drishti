'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { SectionLabel } from '../../components/SectionLabel';
import { Kundli } from '../../components/Kundli';
import { Button } from '../../components/Button';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { getPanchang, wakeBackend, type PanchangQuery } from '../../lib/api';
import { d1ToKundliData, type PanchangResult } from '../../lib/panchang';

interface City {
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

const CITIES: City[] = [
  { label: 'New Delhi', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' },
  { label: 'Mumbai', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { label: 'Bengaluru', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  { label: 'Chennai', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { label: 'Kolkata', latitude: 22.5726, longitude: 88.3639, timezone: 'Asia/Kolkata' },
  { label: 'Hyderabad', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  { label: 'Varanasi', latitude: 25.3176, longitude: 82.9739, timezone: 'Asia/Kolkata' },
  { label: 'London', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { label: 'New York', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { label: 'Dubai', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { label: 'Singapore', latitude: 1.3521, longitude: 103.8198, timezone: 'Asia/Singapore' },
  { label: 'Sydney', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
];

const STORAGE_KEY = 'kavach_panchang_city';

const iso = (d: Date) =>
  new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);

function Panel({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5 ${className}`}>
      <h2 className="mb-3 border-b border-[#A62A34]/25 pb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-[#B39250]">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Row({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-dotted border-[#EEE9DF]/10 py-1.5 last:border-0">
      <span className="text-[#EEE9DF]/60">{label}</span>
      <span className="text-right font-semibold text-[#F7F5F0]">
        {value}
        {sub ? <span className="block text-[11px] font-normal text-[#EEE9DF]/50">{sub}</span> : null}
      </span>
    </div>
  );
}

export default function PanchangPage() {
  const [city, setCity] = useState<City>(CITIES[0]);
  const [date, setDate] = useState<Date>(new Date());
  const [precision, setPrecision] = useState<'min' | 'sec'>('min');
  const [timeStyle, setTimeStyle] = useState<'std' | 'pan'>('std');
  const [data, setData] = useState<PanchangResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    wakeBackend();
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const found = CITIES.find((c) => c.label === stored);
        if (found) setCity(found);
      }
    } catch {
      /* storage unavailable — keep the default city */
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const query: PanchangQuery = {
      date: iso(date),
      latitude: city.latitude,
      longitude: city.longitude,
      timezone: city.timezone,
      label: city.label,
    };
    try {
      setData(await getPanchang(query));
      try {
        window.localStorage.setItem(STORAGE_KEY, city.label);
      } catch {
        /* ignore */
      }
    } catch {
      setError("We couldn't prepare the Panchang right now. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [city, date]);

  useEffect(() => {
    load();
  }, [load]);

  const fmt = useCallback(
    (value?: string | number | null) => {
      if (value === null || value === undefined || value === '') return '—';
      const m = String(value).match(/T(\d{2}):(\d{2})(?::(\d{2}))?/);
      if (!m) return String(value);
      const [, hh, mm, ss] = m;
      if (timeStyle === 'pan') {
        const sunriseHour = Number(String(data?.sun_moon.sunrise || 'T06:').match(/T(\d{2})/)![1]);
        if (Number(hh) < sunriseHour) {
          const total = (Number(hh) + 24) * 3600 + Number(mm) * 60 + Number(ss || 0);
          const H = String(Math.floor(total / 3600)).padStart(2, '0');
          const M = String(Math.floor((total % 3600) / 60)).padStart(2, '0');
          return precision === 'sec' ? `${H}:${M}:${ss || '00'}+` : `${H}:${M}+`;
        }
      }
      return precision === 'sec' ? `${hh}:${mm}:${ss || '00'}` : `${hh}:${mm}`;
    },
    [data, precision, timeStyle],
  );

  const kundli = useMemo(() => (data ? d1ToKundliData(data.d1) : null), [data]);

  const rahu = data?.inauspicious.find((p) => p.name === 'Rahu Kalam');

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-8 sm:py-12">
        {/* KAVACH product intro: keeps the tool reachable without scrolling */}
        <MaskedReveal>
          <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">
            KAVACH <span className="text-[#A62A34]">&bull;</span> Vedic Day Intelligence
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">
            PANCHANG
          </h1>
          <p className="mt-1.5 text-sm text-[#EEE9DF]/60">The Vedic map of the day.</p>
          <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-[#EEE9DF]/45">
            Tithi, Nakshatra, Yoga, Karana, planetary timing and Muhurta for your chosen place and date.
          </p>
          <div className="mt-3 flex items-center gap-4">
            <a href="/ask" className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#EEE9DF]/50 transition-colors hover:text-[#D6BE85]">
              Ask Kavach &rarr;
            </a>
            <a href="/" className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#EEE9DF]/50 transition-colors hover:text-[#D6BE85]">
              &larr; Home
            </a>
          </div>
        </MaskedReveal>

        {/* Controls */}
        <div className="mt-5 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Location</span>
            <select
              value={city.label}
              onChange={(e) => setCity(CITIES.find((c) => c.label === e.target.value) || CITIES[0])}
              className="min-w-[150px] rounded border border-[#A62A34]/35 bg-[#160A0C] px-3 py-2 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
            >
              {CITIES.map((c) => (
                <option key={c.label} value={c.label}>
                  {c.label} · {c.timezone}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Date</span>
            <input
              type="date"
              value={iso(date)}
              onChange={(e) => e.target.value && setDate(new Date(`${e.target.value}T12:00:00`))}
              className="rounded border border-[#A62A34]/35 bg-[#160A0C] px-3 py-2 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
            />
          </label>

          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Precision</span>
            <div className="flex overflow-hidden rounded border border-[#A62A34]/35">
              {(['min', 'sec'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setPrecision(mode)}
                  className={`px-3 py-2 text-[11px] uppercase tracking-wide transition-colors ${
                    precision === mode ? 'bg-[#7B1D26] text-[#F7F5F0]' : 'bg-transparent text-[#EEE9DF]/70 hover:text-[#F7F5F0]'
                  }`}
                >
                  {mode === 'min' ? 'HH:MM' : 'HH:MM:SS'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/50">Time style</span>
            <div className="flex overflow-hidden rounded border border-[#A62A34]/35">
              {(['std', 'pan'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setTimeStyle(mode)}
                  className={`px-3 py-2 text-[11px] uppercase tracking-wide transition-colors ${
                    timeStyle === mode ? 'bg-[#7B1D26] text-[#F7F5F0]' : 'bg-transparent text-[#EEE9DF]/70 hover:text-[#F7F5F0]'
                  }`}
                >
                  {mode === 'std' ? 'Standard' : '24+'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setDate(new Date(date.getTime() - 86400000))}>
              ‹ Prev
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setDate(new Date())}>
              Today
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setDate(new Date(date.getTime() + 86400000))}>
              Next ›
            </Button>
          </div>
        </div>

        {loading && (
          <div className="mt-6 rounded-lg border border-[#A62A34]/40 bg-[#541219]/30 p-4 text-sm">
            Preparing Panchang…
          </div>
        )}

        {!loading && error && (
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[#A62A34]/40 bg-[#541219]/30 p-4 text-sm">
            <span>{error}</span>
            <Button size="sm" variant="primary" onClick={load}>
              Try again
            </Button>
          </div>
        )}

        {!loading && data && (
          <div className="mt-6 space-y-4">
            {/* Rau Kaal — prominent */}
            {rahu && (
              <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[#E53E3E]/45 bg-gradient-to-r from-[#541219]/60 to-[#160A0C]/90 px-5 py-4">
                <div>
                  <div className="font-mono text-[9.5px] uppercase tracking-[0.2em] text-[#E53E3E]">Rahu Kaal</div>
                  <div className="font-mono text-xl font-bold text-[#F7F5F0] sm:text-2xl">
                    {fmt(rahu.start)} → {fmt(rahu.end)}
                  </div>
                </div>
                <div className="font-mono text-[11px] text-[#D6BE85]">{rahu.active ? 'Active now' : dayLabel(rahu, data, new Date())}</div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Panel title="Day overview" className="lg:col-span-2">
                <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
                  {[
                    ['Date', data.day.date],
                    ['Vara', `${data.day.weekday} · ${data.day.vara}`],
                    ['Tithi', `${data.panchanga.tithi.name} · ${data.panchanga.tithi.paksha}`],
                    ['Nakshatra', `${data.panchanga.nakshatra.name} · pada ${data.panchanga.nakshatra.pada}`],
                    ['Yoga', data.panchanga.yoga.name],
                    ['Karana', data.panchanga.karana.current || '—'],
                    ['Moon rashi', data.sun_moon_rashi.moon.name],
                    ['Sun rashi', data.sun_moon_rashi.sun.name],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded border border-[#A62A34]/25 bg-[#090909]/50 px-3 py-2.5">
                      <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-[#EEE9DF]/45">{label}</div>
                      <div className="mt-1 text-sm font-bold text-[#F7F5F0]">{value}</div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Panchanga — current & next" className="lg:col-span-2">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-[13px]">
                    <thead>
                      <tr className="text-left font-mono text-[9px] uppercase tracking-[0.13em] text-[#EEE9DF]/45">
                        <th className="py-1.5">Limb</th>
                        <th>Current</th>
                        <th>Until</th>
                        <th>Next</th>
                      </tr>
                    </thead>
                    <tbody className="text-[#EEE9DF]">
                      {[
                        ['Tithi', data.panchanga.tithi.name, data.panchanga.tithi.end, data.panchanga.tithi.next_name],
                        ['Nakshatra', `${data.panchanga.nakshatra.name} · pada ${data.panchanga.nakshatra.pada}`, data.panchanga.nakshatra.end, data.panchanga.nakshatra.next_name],
                        ['Yoga', data.panchanga.yoga.name, data.panchanga.yoga.end, data.panchanga.yoga.next_name],
                      ].map(([limb, current, end, next]) => (
                        <tr key={String(limb)} className="border-b border-[#EEE9DF]/10">
                          <td className="py-1.5 font-semibold text-[#F7F5F0]">{limb}</td>
                          <td>{current}</td>
                          <td className="font-mono whitespace-nowrap">{fmt(String(end))}</td>
                          <td className="text-[#EEE9DF]/70">{next}</td>
                        </tr>
                      ))}
                      {(data.panchanga.karana.sequence as Array<Record<string, string>>).map((k, i) => (
                        <tr key={String(k.name) + i} className="border-b border-[#EEE9DF]/10 last:border-0">
                          <td className="py-1.5 font-semibold text-[#F7F5F0]">Karana {i + 1}</td>
                          <td>{k.name}{k.is_vishti === 'true' || (k as never as boolean) ? '' : ''}</td>
                          <td className="font-mono whitespace-nowrap">{fmt(k.end)}</td>
                          <td className="text-[#EEE9DF]/70">—</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <Panel title="Sunrise Kundli (D1)" className="lg:col-span-2">
                <p className="mb-3 text-xs text-[#EEE9DF]/60">
                  D1 cast for the exact local sunrise {fmt(data.d1.instant)} · Lagna{' '}
                  <span className="text-[#F7F5F0]">{data.d1.lagna.sign} {data.d1.lagna.degree_in_sign.toFixed(2)}°</span>
                </p>
                {kundli && (
                  <Kundli
                    kundli={kundli}
                    birthDetails={{ date: data.day.date, time: fmt(data.d1.instant), place: data.location.label }}
                    ascendant={data.d1.lagna.sign}
                  />
                )}
              </Panel>

              <Panel title="Planetary positions at sunrise" className="lg:col-span-2">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-[13px]">
                    <thead>
                      <tr className="text-left font-mono text-[9px] uppercase tracking-[0.13em] text-[#EEE9DF]/45">
                        <th className="py-1.5">Planet</th><th>Rashi</th><th>Degree</th><th>Nakshatra</th><th>Pada</th><th>House</th><th>R</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.d1.positions.map((p) => (
                        <tr key={p.planet} className="border-b border-[#EEE9DF]/10 last:border-0">
                          <td className="py-1.5 font-semibold text-[#F7F5F0]">{p.planet}</td>
                          <td>{p.sign}</td>
                          <td className="font-mono">{p.degree_in_sign.toFixed(2)}°</td>
                          <td>{p.nakshatra}</td>
                          <td className="font-mono">{p.pada}</td>
                          <td className="font-mono">{p.house}</td>
                          <td className="font-mono text-[#E53E3E]">{p.retrograde ? 'R' : ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <Panel title="Sun & Moon">
                {([
                  ['Sunrise', data.sun_moon.sunrise],
                  ['Sunset', data.sun_moon.sunset],
                  ['Solar noon', data.sun_moon.solar_noon],
                  ['Next sunrise', data.sun_moon.next_sunrise],
                  ['Moonrise', data.sun_moon.moonrise],
                  ['Moonset', data.sun_moon.moonset],
                ] as Array<[string, string | number | null]>).map(([label, value]) => (
                  <Row key={label} label={label} value={<span className="font-mono">{fmt(value)}</span>} />
                ))}
                <Row label="Day length" value={<span className="font-mono">{(Number(data.sun_moon.day_duration_minutes) / 60).toFixed(3)} h</span>} />
                <Row label="Night length" value={<span className="font-mono">{(Number(data.sun_moon.night_duration_minutes) / 60).toFixed(3)} h</span>} />
              </Panel>

              <Panel title="Planetary Hora">
                {data.hora.current ? (
                  <div className="mb-3 rounded border border-[#B39250]/30 bg-[#090909]/60 px-3 py-2.5">
                    <div className="font-mono text-[9px] uppercase tracking-[0.16em] text-[#D6BE85]">Current hora</div>
                    <div className="text-lg font-bold text-[#F7F5F0]">{data.hora.current.planet}</div>
                    <div className="font-mono text-[11px] text-[#EEE9DF]/60">
                      {fmt(data.hora.current.start)} → {fmt(data.hora.current.end)}
                      {data.hora.next ? ` · next ${data.hora.next.planet} at ${fmt(data.hora.next.start)}` : ''}
                    </div>
                  </div>
                ) : (
                  <Row label="Weekday lord" value={data.hora.weekday_lord} />
                )}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {([['Day Hora', data.hora.day], ['Night Hora', data.hora.night]] as const).map(([label, rows]) => (
                    <div key={label}>
                      <div className="mb-1.5 font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#D6BE85]">{label}</div>
                      <table className="w-full border-collapse text-[12px]">
                        <tbody>
                          {rows.map((h) => (
                            <tr key={h.sequence_number} className={`border-b border-[#EEE9DF]/10 last:border-0 ${h.is_current ? 'bg-[#7B1D26]/30' : ''}`}>
                              <td className={`py-1 font-semibold ${h.is_current ? 'text-[#D6BE85]' : 'text-[#F7F5F0]'}`}>{h.planet}</td>
                              <td className="font-mono whitespace-nowrap">{fmt(h.start)}</td>
                              <td className="font-mono whitespace-nowrap">{fmt(h.end)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Shubha Muhurta">
                {data.auspicious.map((p) => (
                  <div key={p.name} className={`flex items-center justify-between gap-3 border-b border-dotted border-[#EEE9DF]/10 py-1.5 last:border-0 ${p.active ? 'text-[#D6BE85]' : ''}`}>
                    <span className={p.active ? '' : 'text-[#EEE9DF]/60'}>{p.name}</span>
                    <span className="font-mono whitespace-nowrap">{fmt(p.start)} → {fmt(p.end)}</span>
                  </div>
                ))}
              </Panel>

              <Panel title="Ashubha Muhurta">
                {data.inauspicious.map((p) => (
                  <div key={`${p.name}-${p.start}`} className={`flex items-center justify-between gap-3 border-b border-dotted border-[#EEE9DF]/10 py-1.5 last:border-0 ${p.active ? 'text-[#E53E3E]' : ''}`}>
                    <span className={p.active ? '' : 'text-[#EEE9DF]/60'}>{p.name}</span>
                    <span className="font-mono whitespace-nowrap">{fmt(p.start)} → {fmt(p.end)}</span>
                  </div>
                ))}
              </Panel>

              <Panel title="Choghadiya — day">
                <ChoghadiyaTable rows={data.choghadiya.day} fmt={fmt} />
              </Panel>
              <Panel title="Choghadiya — night">
                <ChoghadiyaTable rows={data.choghadiya.night} fmt={fmt} />
              </Panel>

              <Panel title="Chandrabalam & Tarabalam">
                <Row label="Good Chandrabalam (janma rashi)" value={data.balam.good_chandrabalam.length} />
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {data.balam.good_chandrabalam.map((r) => (
                    <span key={r} className="rounded border border-[#B39250]/35 px-2 py-0.5 font-mono text-[10.5px] text-[#D6BE85]">{r}</span>
                  ))}
                </div>
                <div className="mt-4">
                  <Row label="Good Tarabalam (janma nakshatra)" value={data.balam.good_tarabalam.length} />
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {data.balam.good_tarabalam.map((r) => (
                      <span key={r} className="rounded border border-[#B39250]/35 px-2 py-0.5 font-mono text-[10.5px] text-[#D6BE85]">{r}</span>
                    ))}
                  </div>
                </div>
              </Panel>

              <Panel title="Calendar · Ritu · Ayana">
                <Row label="Amanta month" value={String(data.calendar.amanta_month ?? '—')} />
                <Row label="Purnimanta month" value={String(data.calendar.purnimanta_month ?? '—')} />
                <Row label="Vikram Samvat" value={String(data.calendar.vikram_samvat ?? '—')} />
                <Row label="Shaka Samvat" value={String(data.calendar.shaka_samvat ?? '—')} />
                <Row label="Drik Ritu" value={String(data.calendar.ritu_drik ?? '—')} />
                <Row label="Vedic Ritu" value={String(data.calendar.ritu_vedic ?? '—')} />
                <Row label="Drik Ayana" value={String(data.calendar.ayana_drik ?? '—')} />
                <Row label="Vedic Ayana" value={String(data.calendar.ayana_vedic ?? '—')} />
                <Row label="Disha Shoola" value={String(data.calendar.disha_shool ?? '—')} />
              </Panel>
            </div>
          </div>
        )}
      </Container>
    </main>
  );
}

function ChoghadiyaTable({
  rows,
  fmt,
}: {
  rows: Array<{ name: string; classification: string; local_start: string; local_end: string }>;
  fmt: (v?: string | null) => string;
}) {
  const tone = (c: string) => (c === 'bad' ? 'text-[#E53E3E]' : c === 'best' ? 'text-[#8FD3A0]' : 'text-[#D6BE85]');
  return (
    <table className="w-full border-collapse text-[12.5px]">
      <tbody>
        {rows.map((s) => (
          <tr key={`${s.name}-${s.local_start}`} className="border-b border-[#EEE9DF]/10 last:border-0">
            <td className="py-1 font-semibold text-[#F7F5F0]">{s.name}</td>
            <td className={tone(s.classification)}>{s.classification}</td>
            <td className="font-mono whitespace-nowrap">{fmt(s.local_start)}</td>
            <td className="font-mono whitespace-nowrap">{fmt(s.local_end)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function dayLabel(period: { local_start: string }, data: PanchangResult, now: Date) {
  const selected = data.day.date;
  const today = iso(now);
  if (selected !== today) return selected < today ? 'Past' : 'Upcoming';
  const [h, m] = period.local_start.split(':').map(Number);
  const minutes = h * 60 + m;
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  return minutes > nowMinutes ? `Starts in ${minutes - nowMinutes} min` : 'Ended';
}
