'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { isValidPersonName, normalisePersonName } from '../lib/personName';
import {
  BirthProfile,
  createOtherPerson,
  deleteOtherPerson,
  listProfiles,
  updateProfile,
} from '../lib/profiles';

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
const ACTION =
  'inline-flex h-8 items-center rounded border border-[#A62A34]/40 px-3 font-mono text-[9.5px] uppercase tracking-[0.14em] text-[#EEE9DF]/80 transition-colors hover:border-[#A62A34]/70 hover:text-[#F7F5F0] cursor-pointer';

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value || '—';
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' });
}

interface Draft {
  id: string | null;
  isPrimary: boolean;
  name: string;
  birth_date: string;
  birth_time: string;
  birth_place_name: string;
  place: PlaceHit | null;
}

const EMPTY: Draft = {
  id: null,
  isPrimary: false,
  name: '',
  birth_date: '',
  birth_time: '',
  birth_place_name: '',
  place: null,
};

function draftFor(profile: BirthProfile): Draft {
  return {
    id: profile.id,
    isPrimary: profile.is_primary,
    name: profile.name,
    birth_date: profile.birth_date,
    birth_time: profile.birth_time,
    birth_place_name: profile.birth_place_name,
    place: null,
  };
}

/**
 * Account-level birth profiles: the owner's Primary profile plus any number of
 * other people. Other people are always non-primary, and neither creating nor
 * deleting one can change the Primary profile. Editing the Primary keeps it
 * primary and only affects future calculations (history is never touched).
 */
export function BirthProfilesManager({ userId }: { userId: string }) {
  const [profiles, setProfiles] = useState<BirthProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [draft, setDraft] = useState<Draft | null>(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<PlaceHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState('');

  const reload = async () => {
    setLoading(true);
    setLoadError('');
    try {
      setProfiles(await listProfiles(userId));
    } catch (exc) {
      setLoadError(exc instanceof Error ? exc.message : 'We could not load your birth profiles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    const trimmed = query.trim();
    if (!draft || trimmed.length < 3 || trimmed === draft.birth_place_name) {
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
  }, [query, draft]);

  const openNew = () => {
    setDraft({ ...EMPTY });
    setQuery('');
    setHits([]);
    setFormError('');
  };

  const openEdit = (profile: BirthProfile) => {
    setDraft(draftFor(profile));
    setQuery(profile.birth_place_name);
    setHits([]);
    setFormError('');
  };

  const close = () => { setDraft(null); setHits([]); setFormError(''); };

  const pick = (hit: PlaceHit) => {
    if (!draft) return;
    const label = [hit.name, hit.region, hit.country].filter(Boolean).join(', ');
    setDraft({ ...draft, place: hit, birth_place_name: label });
    setQuery(label);
    setHits([]);
  };

  const save = async () => {
    if (!draft || busy) return;
    setFormError('');
    if (!isValidPersonName(draft.name)) { setFormError('Please enter a name.'); return; }
    if (!draft.birth_date || !draft.birth_time) {
      setFormError('Please enter the date and exact time of birth.');
      return;
    }
    if (!draft.place && !draft.id) {
      setFormError('Please select the birth place from the list.');
      return;
    }

    setBusy(true);
    try {
      if (draft.id) {
        const input = {
          name: normalisePersonName(draft.name),
          birth_date: draft.birth_date,
          birth_time: draft.birth_time,
          birth_place_name: draft.birth_place_name,
          ...(draft.place
            ? {
                latitude: draft.place.coordinates.lat,
                longitude: draft.place.coordinates.lng,
                timezone: draft.place.timezone ?? undefined,
              }
            : {}),
        };
        await updateProfile(userId, draft.id, input);
      } else {
        await createOtherPerson(userId, {
          name: normalisePersonName(draft.name),
          birth_date: draft.birth_date,
          birth_time: draft.birth_time,
          birth_place_name: draft.birth_place_name,
          latitude: draft.place!.coordinates.lat,
          longitude: draft.place!.coordinates.lng,
          timezone: draft.place!.timezone ?? undefined,
        });
      }
      close();
      await reload();
    } catch (exc) {
      setFormError(exc instanceof Error ? exc.message : 'We could not save this profile.');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (profile: BirthProfile) => {
    if (profile.is_primary) return;
    if (!window.confirm(`Remove ${profile.name || 'this person'}?`)) return;
    try {
      await deleteOtherPerson(userId, profile.id);
      await reload();
    } catch (exc) {
      setLoadError(exc instanceof Error ? exc.message : 'We could not delete that profile.');
    }
  };

  const primary = profiles.find((profile) => profile.is_primary) ?? null;
  const others = profiles.filter((profile) => !profile.is_primary);

  const renderForm = () => {
    if (!draft) return null;
    return (
      <div className="mt-3 rounded-lg border border-[#A62A34]/30 bg-[#0E0708]/80 p-4">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">
          {draft.id ? 'Edit profile' : 'Add another person'}
        </div>
        <div className="mt-3 space-y-3">
          <div>
            <label className={LABEL} htmlFor="profile-name">Name</label>
            <input id="profile-name" className={FIELD} value={draft.name}
                   onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={LABEL} htmlFor="profile-date">Date of birth</label>
              <input id="profile-date" type="date" className={FIELD} value={draft.birth_date}
                     onChange={(e) => setDraft({ ...draft, birth_date: e.target.value })} />
            </div>
            <div>
              <label className={LABEL} htmlFor="profile-time">Exact birth time</label>
              <input id="profile-time" type="time" className={FIELD} value={draft.birth_time}
                     onChange={(e) => setDraft({ ...draft, birth_time: e.target.value })} />
            </div>
          </div>
          <div>
            <label className={LABEL} htmlFor="profile-place">Birth place</label>
            <input id="profile-place" className={FIELD} value={query} autoComplete="off"
                   placeholder="Search a city"
                   onChange={(e) => {
                     setQuery(e.target.value);
                     setDraft({ ...draft, place: null, birth_place_name: e.target.value });
                   }} />
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
          </div>
        </div>

        {formError && (
          <div role="alert" className="mt-3 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[13px] text-[#EEE9DF]/80">
            {formError}
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-2.5">
          <button type="button" onClick={() => void save()} disabled={busy}
                  className="inline-flex h-9 items-center rounded bg-[#7B1D26] px-5 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50 cursor-pointer">
            {busy ? 'Saving…' : 'Save'}
          </button>
          <button type="button" onClick={close} disabled={busy} className={ACTION}>Cancel</button>
        </div>
      </div>
    );
  };

  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">Your profile</div>

        {loading && <p className="mt-2 text-[13px] text-[#EEE9DF]/55">Loading your profile…</p>}

        {!loading && loadError && (
          <div className="mt-2">
            <p role="alert" className="text-[13px] text-[#EEE9DF]/70">{loadError}</p>
            <button type="button" onClick={() => void reload()} className={`${ACTION} mt-2`}>Retry</button>
          </div>
        )}

        {!loading && !loadError && primary && (
          <div className="mt-2">
            <div className="text-[14px] text-[#F7F5F0]">
              {primary.name}
              <span className="ml-2 font-mono text-[9.5px] uppercase tracking-[0.14em] text-[#B39250]">You · Primary</span>
            </div>
            <div className="mt-1 text-[13px] text-[#EEE9DF]/70">{formatDate(primary.birth_date)} · {primary.birth_time}</div>
            <div className="text-[13px] text-[#EEE9DF]/55">{primary.birth_place_name}</div>
            <div className="mt-3">
              <button type="button" onClick={() => openEdit(primary)} className={ACTION}>Edit</button>
            </div>
          </div>
        )}

        {!loading && !loadError && !primary && (
          <p className="mt-2 text-[13px] text-[#EEE9DF]/60">
            No profile yet. <a href="/profile/setup" className="text-[#B39250] underline">Set up your profile</a>.
          </p>
        )}

        {draft && draft.isPrimary && renderForm()}
      </div>

      <div className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]">Other people</div>

        {others.length === 0 && !draft && (
          <p className="mt-2 text-[13px] text-[#EEE9DF]/55">No other people added yet.</p>
        )}

        {others.length > 0 && (
          <ul className="mt-2 space-y-3">
            {others.map((profile) => (
              <li key={profile.id} className="border-t border-[#A62A34]/15 pt-3 first:border-t-0 first:pt-0">
                <div className="text-[14px] text-[#F7F5F0]">{profile.name}</div>
                <div className="mt-1 text-[13px] text-[#EEE9DF]/70">{formatDate(profile.birth_date)} · {profile.birth_time}</div>
                <div className="text-[13px] text-[#EEE9DF]/55">{profile.birth_place_name}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button type="button" onClick={() => openEdit(profile)} className={ACTION}>Edit</button>
                  <button type="button" onClick={() => void remove(profile)} className={ACTION}>Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {!draft && (
          <div className="mt-4">
            <button type="button" onClick={openNew} className={ACTION}>+ Add another person</button>
          </div>
        )}

        {draft && !draft.isPrimary && renderForm()}
      </div>
    </section>
  );
}
