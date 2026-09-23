'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Container } from '../../../components/Container';
import { Header } from '../../../components/Header';
import { SectionLabel } from '../../../components/SectionLabel';
import { API_BASE, api } from '../../../lib/api';
import { useAuth } from '../../../lib/auth';
import { safeNextPath } from '../../../lib/authPaths';
import { isValidPersonName, normalisePersonName } from '../../../lib/personName';
import { createPrimaryProfile, getPrimaryProfile } from '../../../lib/profiles';

interface PlaceHit {
  id: string;
  name: string;
  region: string;
  country: string;
  coordinates: { lat: number; lng: number };
  timezone?: string | null;
}

const FIELD =
  'mt-1 w-full rounded border border-[#A62A34]/35 bg-[#0E0708] px-3 py-2.5 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]';
const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

/**
 * One-time account-owner setup. This page must NEVER require a Primary Profile
 * (it creates it), so it is not wrapped in the shared profile guard.
 */
export default function ProfileSetupPage() {
  const router = useRouter();
  const { status, user } = useAuth();
  const [name, setName] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [place, setPlace] = useState<PlaceHit | null>(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<PlaceHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [next, setNext] = useState('/daily');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setNext(safeNextPath(params.get('next')));
  }, []);

  // A user who already has a Primary Profile is never asked again.
  useEffect(() => {
    if (status !== 'signedIn' || !user) return;
    let active = true;
    (async () => {
      try {
        const existing = await getPrimaryProfile(user.id);
        if (active && existing) router.replace(next);
      } catch {
        // A load failure must not block setup; the user can still create one.
      }
    })();
    return () => { active = false; };
  }, [status, user, next, router]);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 3 || trimmed === place?.name) {
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
  }, [query, place]);

  const pick = (hit: PlaceHit) => {
    setPlace(hit);
    setQuery([hit.name, hit.region, hit.country].filter(Boolean).join(', '));
    setHits([]);
  };

  const submit = async () => {
    if (busy) return;
    setError('');
    if (!isValidPersonName(name)) { setError('Please enter your name.'); return; }
    if (!date || !time) { setError('Please enter your date and time of birth.'); return; }
    if (!place) { setError('Please select your birth place from the list.'); return; }
    if (status !== 'signedIn' || !user) { setError('Please sign in again to continue.'); return; }

    setBusy(true);
    try {
      await createPrimaryProfile(user.id, {
        name: normalisePersonName(name),
        birth_date: date,
        birth_time: time,
        birth_place_name: query || place.name,
        latitude: place.coordinates.lat,
        longitude: place.coordinates.lng,
        timezone: place.timezone ?? undefined,
      });
      router.replace(next);
    } catch (exc) {
      // The form is kept exactly as entered; nothing claims to be saved.
      setError(exc instanceof Error ? exc.message : 'We could not save your profile. Please try again.');
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="md" className="py-12 sm:py-16">
        <SectionLabel label="KAVACH · Your Profile" tone="brass" />
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.04em] text-[#F7F5F0] sm:text-3xl">
          Set up your birth profile
        </h1>
        <p className="mt-2 max-w-xl text-[13.5px] leading-relaxed text-[#EEE9DF]/60">
          KAVACH uses these details as the base for your personal readings.
        </p>

        <section className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 sm:p-6">
          <div className="space-y-4">
            <div>
              <label className={LABEL} htmlFor="setup-name">Your name</label>
              <input id="setup-name" className={FIELD} value={name}
                     onChange={(e) => setName(e.target.value)} placeholder="Enter your name" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className={LABEL} htmlFor="setup-date">Date of birth</label>
                <input id="setup-date" type="date" className={FIELD} value={date}
                       onChange={(e) => setDate(e.target.value)} />
              </div>
              <div>
                <label className={LABEL} htmlFor="setup-time">Exact birth time</label>
                <input id="setup-time" type="time" className={FIELD} value={time}
                       onChange={(e) => setTime(e.target.value)} />
                <p className="mt-1 text-[11px] text-[#EEE9DF]/45">Use your recorded birth time where possible.</p>
              </div>
            </div>
            <div>
              <label className={LABEL} htmlFor="setup-place">Birth place</label>
              <input id="setup-place" className={FIELD} value={query} autoComplete="off"
                     placeholder="Search a city"
                     onChange={(e) => { setQuery(e.target.value); setPlace(null); }} />
              {searching && <p className="mt-1 text-[11px] text-[#EEE9DF]/40">Searching…</p>}
              {hits.length > 0 && (
                <ul className="mt-1 overflow-hidden rounded border border-[#A62A34]/30 bg-[#0E0708]">
                  {hits.map((hit) => (
                    <li key={hit.id}>
                      <button type="button" onClick={() => pick(hit)}
                              className="block w-full px-3 py-2 text-left text-[13px] text-[#EEE9DF]/80 hover:bg-[#2B0C11]/60">
                        {[hit.name, hit.region, hit.country].filter(Boolean).join(', ')}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {place && <p className="mt-1 text-[11px] text-[#EEE9DF]/40">Selected: {query}</p>}
            </div>
          </div>

          {error && (
            <div role="alert" className="mt-4 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
              {error}
            </div>
          )}

          <div className="mt-6">
            <button type="button" onClick={() => void submit()} disabled={busy}
                    className="inline-flex h-11 items-center justify-center rounded bg-[#7B1D26] px-8 font-mono text-[11px] uppercase tracking-[0.18em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50">
              {busy ? 'Saving…' : 'Create My Profile'}
            </button>
          </div>
        </section>
      </Container>
    </main>
  );
}
