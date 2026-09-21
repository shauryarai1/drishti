'use client';

import React, { useMemo, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import {
  fetchWeekly,
  searchWeeklyPlaces,
  type WeeklyForecast,
  type WeeklyPlace,
} from '../../lib/weekly';

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70';
const FIELD = 'mt-1 w-full rounded border border-[#A62A34]/35 bg-[#0E0708] px-3 py-2.5 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';

// Subtle tone treatment - guidance, never an alarm.
const TONE: Record<string, { border: string; text: string; chip: string }> = {
  supportive: { border: 'border-[#7BD88F]/25', text: 'text-[#7BD88F]', chip: 'bg-[#7BD88F]/10' },
  personal: { border: 'border-[#D6BE85]/25', text: 'text-[#D6BE85]', chip: 'bg-[#D6BE85]/10' },
  caution: { border: 'border-[#E5B567]/25', text: 'text-[#E5B567]', chip: 'bg-[#E5B567]/10' },
  strong_caution: { border: 'border-[#E5B567]/40', text: 'text-[#E5B567]', chip: 'bg-[#E5B567]/15' },
};

function todayLocal(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function prettyDate(iso: string): string {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }).toUpperCase();
}

function weekday(iso: string, length: 'short' | 'long' = 'short'): string {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', { weekday: length }).toUpperCase();
}

function timeText(value: string): string {
  if (!value) return '';
  if (value === '00:00') return 'Start of day';
  return value;
}

function endText(value: string): string {
  if (!value || value === '00:00') return 'Rest of the day';
  return `Until ${value}`;
}

function PlaceField({ label, value, onResolve, placeholder }: {
  label: string; value: WeeklyPlace | null; onResolve: (place: WeeklyPlace | null, raw: string) => void;
  placeholder: string;
}) {
  const [text, setText] = useState(value?.label ?? '');
  const [options, setOptions] = useState<WeeklyPlace[]>([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [noMatch, setNoMatch] = useState(false);

  // Debounced autocomplete through the existing KAVACH place search API.
  React.useEffect(() => {
    if (value) return;                       // already resolved: no need to search
    const trimmed = text.trim();
    setNoMatch(false);
    if (trimmed.length < 3) {                // backend requires 3+ characters
      setOptions([]);
      setOpen(false);
      return;
    }
    let cancelled = false;
    setBusy(true);
    const timer = setTimeout(async () => {
      const found = await searchWeeklyPlaces(trimmed);
      if (cancelled) return;
      setOptions(found);
      setOpen(found.length > 0);
      setHighlight(found.length > 0 ? 0 : -1);
      setNoMatch(found.length === 0);
      setBusy(false);
    }, 250);
    return () => { cancelled = true; clearTimeout(timer); setBusy(false); };
  }, [text, value]);

  const choose = (place: WeeklyPlace) => {
    onResolve(place, place.label);
    setText(place.label);
    setOptions([]);
    setOpen(false);
    setNoMatch(false);
  };

  const onChange = (next: string) => {
    setText(next);
    if (value && next !== value.label) onResolve(null, next);  // stale coordinates must not survive
    setOpen(false);
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || options.length === 0) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlight((current) => (current + 1) % options.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((current) => (current - 1 + options.length) % options.length);
    } else if (event.key === 'Enter' && highlight >= 0) {
      event.preventDefault();
      choose(options[highlight]);
    } else if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <label className="relative block">
      <span className={LABEL}>{label}</span>
      <input
        className={FIELD}
        value={text}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
        onFocus={() => { if (options.length > 0) setOpen(true); }}
        onBlur={() => setTimeout(() => setOpen(false), 140)}
      />
      {busy && <span className="mt-1 block text-[11px] text-[#EEE9DF]/40">Searching&hellip;</span>}
      {value && (
        <span className="mt-1 block text-[11px] text-[#7BD88F]">
          {value.label} &middot; {value.latitude.toFixed(3)}, {value.longitude.toFixed(3)}
        </span>
      )}
      {!value && !busy && noMatch && (
        <span className="mt-1 block text-[11px] text-[#E5B567]">
          No matching place found. Try a nearby city or region.
        </span>
      )}
      {open && options.length > 0 && (
        <ul className="absolute z-30 mt-1 max-h-64 w-full overflow-auto rounded border border-[#A62A34]/40 bg-[#160A0C] shadow-[0_20px_60px_rgba(0,0,0,0.85)]">
          {options.map((option, index) => (
            <li key={`${option.label}-${index}`}>
              <button
                type="button"
                onMouseDown={(event) => { event.preventDefault(); choose(option); }}
                onMouseEnter={() => setHighlight(index)}
                className={`block w-full px-3 py-2 text-left text-[12.5px] leading-snug ${
                  index === highlight ? 'bg-[#2B0C11] text-[#F7F5F0]' : 'text-[#EEE9DF]/75'
                }`}
              >
                {option.label}
                <span className="ml-2 font-mono text-[10px] text-[#EEE9DF]/35">
                  {option.latitude.toFixed(2)}, {option.longitude.toFixed(2)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  );
}

export default function YourWeekPage() {
  const [birthDate, setBirthDate] = useState('1990-05-15');
  const [birthTime, setBirthTime] = useState('14:15');
  const [birthPlace, setBirthPlace] = useState<WeeklyPlace | null>(null);
  const [startDate, setStartDate] = useState(todayLocal());
  const [forecastPlace, setForecastPlace] = useState<WeeklyPlace | null>(null);
  const [week, setWeek] = useState<WeeklyForecast | null>(null);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const selectedDay = week?.days[selected] ?? null;

  const range = useMemo(() => {
    if (!week) return '';
    return `${prettyDate(week.startDate)} — ${prettyDate(week.endDate)}`;
  }, [week]);

  const reveal = async () => {
    setError('');
    if (!birthDate || !birthTime) {
      setError('Please add the date and exact time of birth.');
      return;
    }
    if (!birthPlace) {
      setError('Please select a valid birth place.');
      return;
    }
    if (!forecastPlace) {
      setError('Please select a valid forecast location.');
      return;
    }
    setBusy(true);
    setWeek(null);
    try {
      const result = await fetchWeekly({
        birth: { date: birthDate, time: birthTime, place: birthPlace.label,
                 latitude: birthPlace.latitude, longitude: birthPlace.longitude,
                 timezone: birthPlace.timezone },
        forecast: { startDate, place: forecastPlace.label,
                    latitude: forecastPlace.latitude, longitude: forecastPlace.longitude,
                    timezone: forecastPlace.timezone },
      });
      setWeek(result);
      setSelected(0);
    } catch (exc) {
      setError(exc instanceof Error && exc.message
        ? exc.message
        : "We couldn't prepare your week with those details. Check your birth and location information and try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-8 sm:py-12">
        <MaskedReveal>
          <div className="flex items-center gap-3">
            <span className="rounded border border-[#B39250]/40 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.2em] text-[#B39250]">
              Premium
            </span>
            <span className={LABEL}>KAVACH <span className="text-[#A62A34]">&bull;</span> Personal Guidance</span>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-4xl">YOUR WEEK</h1>
          <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-[#EEE9DF]/55">
            See the rhythm of your next seven days &mdash; when to move forward, when to take things slowly,
            and when support may be easier to find.
          </p>
        </MaskedReveal>

        {!week && (
          <section className={`${PANEL} mt-6 p-5`}>
            <div className={LABEL}>Your Birth Details</div>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className={LABEL}>Date of Birth</span>
                <input type="date" className={FIELD} value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
              </label>
              <label className="block">
                <span className={LABEL}>Exact Birth Time</span>
                <input type="time" className={FIELD} value={birthTime} onChange={(e) => setBirthTime(e.target.value)} />
                <span className="mt-1 block text-[11px] text-[#EEE9DF]/35">
                  Your birth time helps KAVACH prepare your personal forecast.
                </span>
              </label>
              <div className="sm:col-span-2">
                <PlaceField label="Birth Place" value={birthPlace} onResolve={setBirthPlace} placeholder="Search birth place" />
              </div>
            </div>

            <div className={`${LABEL} mt-6`}>Your Forecast</div>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className={LABEL}>Starting From</span>
                <input type="date" className={FIELD} value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </label>
              <PlaceField label="Forecast Location" value={forecastPlace} onResolve={setForecastPlace} placeholder="Search forecast location" />
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-4">
              <button
                onClick={reveal}
                disabled={busy}
                className="rounded bg-[#7B1D26] px-5 py-3 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50"
              >
                {busy ? 'Preparing your week…' : 'Reveal My Week'}
              </button>
              {busy && <span className="text-[12px] text-[#EEE9DF]/50">Mapping the next seven days&hellip;</span>}
            </div>

            <p className="mt-4 text-[11px] leading-relaxed text-[#EEE9DF]/35">
              Your birth details are used to prepare this personalized forecast.
            </p>

            {error && (
              <div className="mt-4 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
                {error}
              </div>
            )}
          </section>
        )}

        {busy && !week && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {[0, 1].map((index) => <div key={index} className={`${PANEL} h-40 animate-pulse opacity-40`} />)}
          </div>
        )}

        {week && selectedDay && (
          <>
            <div className="mt-6 flex flex-wrap items-end justify-between gap-3">
              <div>
                <div className={LABEL}>Your Week</div>
                <div className="mt-1 text-xl font-semibold tracking-[0.08em] text-[#F7F5F0]">{range}</div>
              </div>
              <button
                onClick={() => { setWeek(null); setSelected(0); }}
                className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/50 hover:text-[#D6BE85]"
              >
                Change details
              </button>
            </div>

            <section className={`${PANEL} mt-3 p-4`}>
              <p className="text-[13.5px] leading-relaxed text-[#EEE9DF]/75">{week.weekSummary}</p>
            </section>

            {week.highlights.length > 0 && (
              <section className="mt-5">
                <div className={LABEL}>Week Highlights</div>
                <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {week.highlights.map((item) => (
                    <div key={`${item.label}-${item.date}`} className={`${PANEL} p-3`}>
                      <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85]">{item.label}</div>
                      <div className="mt-1 text-[11.5px] text-[#EEE9DF]/50">
                        {weekday(item.date, 'long')} &middot; {prettyDate(item.date)}
                        {item.time && item.time !== '00:00' ? ` · from ${item.time}` : ''}
                      </div>
                      <p className="mt-2 text-[12.5px] leading-relaxed text-[#EEE9DF]/70">{item.text}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="mt-6">
              <div className={LABEL}>Seven Days</div>
              <div className="-mx-1 mt-2 overflow-x-auto px-1 pb-1">
                <div className="flex min-w-max gap-1.5">
                  {week.days.map((day, index) => (
                    <button
                      key={day.date}
                      onClick={() => setSelected(index)}
                      aria-pressed={selected === index}
                      className={`min-w-[74px] rounded border px-3 py-2 text-center transition-colors ${
                        selected === index
                          ? 'border-[#A62A34]/70 bg-[#7B1D26] text-[#F7F5F0]'
                          : 'border-[#A62A34]/25 text-[#EEE9DF]/55 hover:text-[#D6BE85]'
                      }`}
                    >
                      <div className="font-mono text-[9.5px] tracking-[0.16em]">{weekday(day.date)}</div>
                      <div className="mt-0.5 text-[15px]">{day.date.slice(8, 10)}</div>
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <section className={`${PANEL} mt-4 p-5`}>
              <div className={LABEL}>{weekday(selectedDay.date, 'long')}</div>
              <div className="mt-1 text-[13px] text-[#EEE9DF]/55">{prettyDate(selectedDay.date)}</div>
              <h2 className="mt-3 text-lg font-semibold leading-snug text-[#F7F5F0] sm:text-xl">{selectedDay.headline}</h2>
              <p className="mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/75">{selectedDay.summary}</p>

              <div className="mt-4 space-y-3">
                {selectedDay.periods.map((period, index) => {
                  const tone = TONE[period.tone] ?? TONE.personal;
                  return (
                    <article key={`${period.start}-${index}`} className={`rounded border ${tone.border} bg-[#0E0708]/50 p-4`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className={`inline-flex items-center gap-2 rounded px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] ${tone.chip} ${tone.text}`}>
                          {index === 0 ? 'Before' : 'After'} {period.start === '00:00' ? 'Start of day' : period.start}
                        </span>
                        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#EEE9DF]/40">
                          {endText(period.end)}
                        </span>
                      </div>
                      <div className="mt-2 text-[13.5px] font-semibold text-[#F7F5F0]">{period.headline}</div>
                      <p className="mt-1 text-[13px] leading-relaxed text-[#EEE9DF]/70">{period.guidance}</p>
                      <div className="mt-1 text-[10.5px] text-[#EEE9DF]/30">{weekday(selectedDay.date, 'long')} · {period.label}</div>
                    </article>
                  );
                })}
              </div>
            </section>

            <p className="mt-5 text-[11px] leading-relaxed text-[#EEE9DF]/35">
              Your week describes tendencies for the days ahead rather than fixed events. It is guidance, not a guarantee.
            </p>
          </>
        )}
      </Container>
    </main>
  );
}
