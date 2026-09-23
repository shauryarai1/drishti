'use client';

import React from 'react';
import Link from 'next/link';
import type { BirthProfile } from '../lib/profiles';

/**
 * Subtle person selector. Every fresh visit defaults to the Primary Profile;
 * choosing another person is local to this feature and never becomes the
 * account default. There is deliberately no "Make Primary" action.
 */
export function PersonSelector({
  profiles,
  selectedId,
  onChange,
}: {
  profiles: BirthProfile[];
  selectedId: string;
  onChange: (id: string) => void;
}) {
  if (profiles.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]" htmlFor="person-select">
        Reading for
      </label>
      <select
        id="person-select"
        value={selectedId}
        onChange={(event) => onChange(event.target.value)}
        className="rounded border border-[#A62A34]/35 bg-[#0E0708] px-3 py-2 text-[13px] text-[#F7F5F0] outline-none focus:border-[#A62A34]"
      >
        {profiles.map((profile) => (
          <option key={profile.id} value={profile.id}>
            {profile.is_primary ? `${profile.name} (You · Primary)` : profile.name}
          </option>
        ))}
      </select>
      <Link href="/account" className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] hover:text-[#F7F5F0]">
        + Add another person
      </Link>
    </div>
  );
}
