'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { RequireProfile } from '../../components/RequireProfile';
import { PersonSelector } from '../../components/PersonSelector';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { useAuth } from '../../lib/auth';
import { deriveNatal } from '../../lib/natal';
import { listProfiles, type BirthProfile } from '../../lib/profiles';
import {
  DAILY_CITIES,
  MOON_SIGNS,
  fetchDaily,
  type DailyCard,
  type DailyResponse,
  type DailyStatus,
} from '../../lib/daily';

const CITY_KEY = 'kavach_panchang_city';
const SIGN_KEY = 'kavach_daily_moon_sign';

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70';

const STATUS_STYLE: Record<DailyStatus, { dot: string; text: string }> = {
  GOOD: { dot: 'bg-[#7BD88F]', text: 'text-[#7BD88F]' },
  NEUTRAL: { dot: 'bg-[#D6BE85]', text: 'text-[#D6BE85]' },
  CAUTION: { dot: 'bg-[#E5B567]', text: 'text-[#E5B567]' },
};

function StatusPill({ status }: { status: DailyStatus }) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.NEUTRAL;
  return (
    <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] ${style.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {status}
    </span>
  );
}

function CategoryRow({ label, status, reason }: { label: string; status: DailyStatus; reason: string }) {
  return (
    <div className="border-t border-[#A62A34]/15 pt-2">
      <div className="flex items-center justify-between gap-3">
        <span className={LABEL}>{label}</span>
        <StatusPill status={status} />
      </div>
      <p className="mt-1 text-[12.5px] leading-relaxed text-[#EEE9DF]/55">{reason}</p>
    </div>
  );
}

/**
 * The user's LOCAL calendar date for a timezone: the Daily reading day runs
 * midnight to midnight in that zone, so the server must never fall back to its
 * own clock (or UTC).
 */
function localCalendarDate(timeZone: string): string {
  try {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    }).format(new Date());
  } catch {
    // Unknown zone: fall back to the device's own local date.
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  }
}

function DailyContent() {
  const { user } = useAuth();
  const [profiles, setProfiles] = useState<BirthProfile[]>([]);
  const [selectedId, setSelectedId] = useState('');
  // Natal values are derived from the selected profile's birth facts and are
  // never stored. `natalRef` keeps them out of the load() dependency list.
  const natalRef = useRef<{ moonRashi: string; janmaNakshatra: string } | null>(null);
  const natalRequestIdRef = useRef(0);
  const bootstrappedRef = useRef(false);
  const [city, setCity] = useState(DAILY_CITIES[0]);
  const [data, setData] = useState<DailyResponse | null>(null);
  const [selected, setSelected] = useState<string>('');
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  // A profile/natal failure is surfaced with a retry. Daily never falls back to
  // another person, a saved reading or fabricated natal data.
  const [profileError, setProfileError] = useState('');
  const dayRef = useRef<string>('');
  // Latest-wins guard: a slow response for a previously selected city must never
  // overwrite the reading for the city the user is looking at now.
  const requestIdRef = useRef(0);

  const load = useCallback(async (label: string) => {
    const found = DAILY_CITIES.find((item) => item.label === label) ?? DAILY_CITIES[0];
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setCity(found);
    setBusy(true);
    setError('');
    try {
        const localDate = localCalendarDate(found.timezone);
        dayRef.current = localDate;
        const result = await fetchDaily({
          latitude: found.latitude,
          longitude: found.longitude,
          // The daily Moon is the Moon at LOCAL sunrise, so the request must use
          // the selected city's own timezone (not a single hardcoded zone).
          timezone: found.timezone,
          // The reading day is the user's LOCAL calendar date: midnight to
          // midnight. Sending it makes the requested day authoritative instead
          // of relying on the server's clock.
          date: localDate,
          // Personal layer: the selected profile's natal Moon Rashi and Janma
          // Nakshatra (derived from its birth facts by the authoritative engine).
          ...(natalRef.current
            ? { natal_moon: natalRef.current.moonRashi,
                natal_nakshatra: natalRef.current.janmaNakshatra }
            : {}),
        });
        if (requestId !== requestIdRef.current) return;   // a newer request won
        setData(result);
    } catch {
      if (requestId !== requestIdRef.current) return;     // a newer request won
      setData(null);
      setError("Today's prediction is temporarily unavailable. Please try again.");
    } finally {
      if (requestId === requestIdRef.current) setBusy(false);
    }
  }, []);

  // The Daily reading must roll over exactly at LOCAL midnight, even in a tab
  // that is left open. Re-check the local calendar date periodically and on
  // return to the tab; only refetch when the day actually changed.
  useEffect(() => {
    const check = () => {
      const current = localCalendarDate(city.timezone);
      if (dayRef.current && current !== dayRef.current) {
        void load(city.label);
      }
    };
    const timer = setInterval(check, 30_000);
    document.addEventListener('visibilitychange', check);
    window.addEventListener('focus', check);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', check);
      window.removeEventListener('focus', check);
    };
  }, [city.timezone, city.label, load]);

  useEffect(() => {
    let storedCity = DAILY_CITIES[0].label;
    let storedSign = '';
    try {
      storedCity = window.localStorage.getItem(CITY_KEY) || storedCity;
      storedSign = window.localStorage.getItem(SIGN_KEY) || '';
    } catch {
      /* storage unavailable */
    }
    if (storedSign) setSelected(storedSign);
    void load(storedCity);
  }, [load]);

  // The Daily location is kept in a ref so the profile bootstrap below never
  // depends on it (which would re-run the effect).
  const cityRef = useRef(city.label);
  cityRef.current = city.label;

  // Default to the account's PRIMARY profile. A fresh visit always starts with
  // Primary; an explicit selection is local to this visit only.
  const bootstrap = useCallback(async () => {
    if (!user) return;
    setProfileError('');
    try {
      const list = await listProfiles(user.id);
      setProfiles(list);
      const primary = list.find((profile) => profile.is_primary);
      if (!primary) {
        // Never fall back to the first other person: the account owner needs a
        // Primary Profile before a personal Daily can be shown.
        setProfileError('We could not find your Primary Profile. Please set it up to see your personal Daily.');
        return;
      }
      setSelectedId(primary.id);
      const requestId = natalRequestIdRef.current + 1;
      natalRequestIdRef.current = requestId;
      let natal: { moonRashi: string; janmaNakshatra: string } | null = null;
      try {
        natal = await deriveNatal(primary);
      } catch {
        natal = null;
      }
      if (requestId !== natalRequestIdRef.current) return;
      if (!natal) {
        // Never fabricate natal data, and never borrow another person's.
        natalRef.current = null;
        setProfileError('We could not calculate your personal reading. Please try again.');
        return;
      }
      natalRef.current = natal;
      await load(cityRef.current);
    } catch {
      // A profile load failure must never fall back to a saved reading or
      // another person; the user gets a retry instead.
      natalRef.current = null;
      setProfileError('We could not load your birth profile. Please try again.');
    }
  }, [user, load]);

  useEffect(() => {
    if (!user || bootstrappedRef.current) return;
    bootstrappedRef.current = true;
    void bootstrap();
  }, [user, bootstrap]);

  const retryProfile = () => {
    bootstrappedRef.current = false;
    void bootstrap();
  };

  const selectPerson = (id: string) => {
    const profile = profiles.find((item) => item.id === id);
    if (!profile || id === selectedId) return;
    const previousId = selectedId;
    setSelectedId(id);
    setProfileError('');
    const requestId = natalRequestIdRef.current + 1;
    natalRequestIdRef.current = requestId;
    void (async () => {
      let natal: { moonRashi: string; janmaNakshatra: string } | null = null;
      try {
        natal = await deriveNatal(profile);
      } catch {
        natal = null;
      }
      if (requestId !== natalRequestIdRef.current) return;   // latest wins
      if (!natal) {
        // Do not leave another person's reading labelled with this name.
        natalRef.current = null;
        setSelectedId(previousId);
        setProfileError('We could not calculate that person\u2019s reading. Please try again.');
        return;
      }
      natalRef.current = natal;
      await load(cityRef.current);
    })();
  };

  const chooseSign = (sign: string) => {
    setSelected(sign);
    try {
      window.localStorage.setItem(SIGN_KEY, sign);
    } catch {
      /* ignore */
    }
    document.getElementById(`sign-${sign}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const updated = useMemo(() => {
    if (!data) return '';
    const date = new Date(data.asOf.timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: 'numeric', minute: '2-digit' });
  }, [data]);

  const cards: DailyCard[] = data?.signs ?? [];

  return (
    <RequireProfile>
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-8 sm:py-12">
        <MaskedReveal>
          <div className={LABEL}>
            KAVACH <span className="text-[#A62A34]">&bull;</span> Vedic Day Intelligence
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">DAILY PREDICTION</h1>
          <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-[#EEE9DF]/50">
            See how today&apos;s Moon movement shapes the pattern of the day for each Moon sign.
          </p>
        </MaskedReveal>

        {profileError && (
          <section className={`${PANEL} mt-5 p-4`}>
            <div className="text-[13px] text-[#EEE9DF]/80">{profileError}</div>
            <button
              onClick={retryProfile}
              className="mt-3 rounded bg-[#7B1D26] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] hover:bg-[#A62A34]"
            >
              Retry
            </button>
          </section>
        )}

        <section className={`${PANEL} mt-5 p-4`}>
          {busy && !data ? (
            <div className="text-[13px] text-[#EEE9DF]/55">Reading today&apos;s Moon pattern&hellip;</div>
          ) : data ? (
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <div className={LABEL}>Daily Moon</div>
                <div className="mt-1 text-[15px] text-[#F7F5F0]">{data.dailyMoon.rashi}</div>
                <div className="mt-0.5 text-[11px] text-[#EEE9DF]/40">at local sunrise</div>
              </div>
              <div>
              {profiles.length > 0 && (
              <div className="mb-5">
                <PersonSelector profiles={profiles} selectedId={selectedId} onChange={selectPerson} />
              </div>
            )}
              <div className={LABEL}>Date</div>
                <div className="mt-1 text-[15px] text-[#F7F5F0]">{data.dailyMoon.date}</div>
              {data.nakshatra?.name && (
                <div className="mt-3">
                  <div className={LABEL}>Moon Nakshatra</div>
                  <div className="mt-1 text-[15px] text-[#F7F5F0]">{data.nakshatra.name}</div>
                  {data.nakshatra.mode && (
                    <p className="mt-1 text-[12px] leading-relaxed text-[#EEE9DF]/55">
                      {data.nakshatra.mode}
                    </p>
                  )}
                </div>
              )}
              </div>
              <div>
                <div className={LABEL}>Updated</div>
                <div className="mt-1 text-[15px] text-[#F7F5F0]">{updated}</div>
              </div>
            </div>
          ) : (
            <div className="text-[13px] text-[#EEE9DF]/55">Today&apos;s pattern is shown below.</div>
          )}
        </section>

        <section className="mt-5">
          <div className={LABEL}>Your Moon Sign</div>
          <div className="-mx-1 mt-2 overflow-x-auto px-1">
            <div className="flex min-w-max gap-1.5 pb-1">
              {MOON_SIGNS.map((sign) => (
                <button
                  key={sign}
                  onClick={() => chooseSign(sign)}
                  aria-pressed={selected === sign}
                  className={`rounded px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] transition-colors ${
                    selected === sign ? 'bg-[#7B1D26] text-[#F7F5F0]' : 'text-[#EEE9DF]/50 hover:text-[#D6BE85]'
                  }`}
                >
                  {sign}
                </button>
              ))}
            </div>
          </div>
        </section>

        {error && (
          <section className={`${PANEL} mt-5 p-4`}>
            <div className="text-[13px] text-[#EEE9DF]/80">{error}</div>
            <button
              onClick={() => load(city.label)}
              className="mt-3 rounded bg-[#7B1D26] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] hover:bg-[#A62A34]"
            >
              Retry
            </button>
          </section>
        )}

        {busy && !data && !error && (
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {MOON_SIGNS.map((sign) => (
              <div key={sign} className={`${PANEL} h-56 animate-pulse p-4 opacity-40`} />
            ))}
          </div>
        )}

        {cards.length > 0 && (
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => {
              const isSelected = selected === card.sign;
              return (
                <article
                  key={card.sign}
                  id={`sign-${card.sign}`}
                  className={`${PANEL} p-4 transition-colors ${
                    isSelected ? 'border-[#A62A34]/70 bg-[#1C0B0E]/80' : ''
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <h2 className="text-[15px] font-semibold uppercase tracking-[0.14em] text-[#F7F5F0]">{card.sign}</h2>
                    {card.isPersonal && <span className={LABEL}>Your sign</span>}
                  </div>
                  <div className={`${LABEL} mt-3`}>Today&apos;s Pattern</div>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-[#EEE9DF]/75">{card.pattern}</p>

                  <div className="mt-4 space-y-2.5">
                    <CategoryRow label="Love" status={card.categories.love.status} reason={card.categories.love.reason} />
                    <CategoryRow label="Health" status={card.categories.health.status} reason={card.categories.health.reason} />
                    <CategoryRow label="Career" status={card.categories.career.status} reason={card.categories.career.reason} />
                  </div>

                  {card.bestColour && (
                    <div className="mt-3 flex items-center justify-between border-t border-[#A62A34]/15 pt-2">
                      <span className={LABEL}>Best Colour</span>
                      <span className="text-[12.5px] text-[#F7F5F0]">{card.bestColour}</span>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}

        <p className="mt-6 text-[11px] leading-relaxed text-[#EEE9DF]/35">
          Daily patterns describe tendencies for the day rather than fixed events. They are guidance, not guarantees.
        </p>
      </Container>
    </main>
    </RequireProfile>
  );
}

export default function DailyPage() {
  return <DailyContent />;
}
