'use client';

import React, { useState } from 'react';
import type {
  BnnConnection,
  KundliResponse,
  MalaShreeChain,
  RelationshipQuality,
} from '../../lib/kundli';

// BNN Connections + Mala-Shree. Connections are grouped mechanically by the
// backend; relationship quality is only an annotation, so an ENEMY connection
// is still shown as a present connection.

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const PANEL = 'rounded-lg border border-[#A62A24]/25 bg-[#160A0C]/70';
const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

const GROUPS: Array<{ key: string; title: string; positions: number[]; note: string }> = [
  { key: 'TRINE_SUPPORT', title: 'Trine / Core', positions: [1, 5, 9], note: 'Support & karakatwa blending' },
  { key: 'FUTURE', title: 'Future / Forward', positions: [2], note: 'Future / forward development' },
  { key: 'PAST', title: 'Past / Background', positions: [12], note: 'Past / background' },
  { key: 'STRUGGLE', title: 'Struggle / Effort', positions: [3], note: 'Struggle / effort' },
  { key: 'GAIN', title: 'Gain / Result', positions: [11], note: 'Gain / result' },
  { key: 'OPPOSITION_COMPLETION', title: 'Opposition & Completion', positions: [7], note: 'Opposition & completion' },
];

const QUALITY_TEXT: Record<RelationshipQuality, string> = {
  FRIEND: 'Friend relationship',
  ENEMY: 'Enemy relationship',
  NEUTRAL: 'Neutral relationship',
};

const QUALITY_CLASS: Record<RelationshipQuality, string> = {
  FRIEND: 'border-[#7BD88F]/30 text-[#7BD88F]',
  ENEMY: 'border-[#E5B567]/35 text-[#E5B567]',
  NEUTRAL: 'border-[#EEE9DF]/20 text-[#EEE9DF]/55',
};

const LAYER_TEXT: Record<string, string> = {
  ACTUAL_POSITION: 'Actual position',
  RETRO_PREVIOUS_POSITION: 'Retrograde previous-sign position',
  DIRECT_POSITION: 'Direct position',
  DISPOSITOR_OPERATIONAL: 'Dispositor / operational position',
};

function ordinal(value: number): string {
  const suffix = value === 1 ? 'st' : value === 2 ? 'nd' : value === 3 ? 'rd' : 'th';
  return `${value}${suffix}`;
}

function ConnectionCard({ row }: { row: BnnConnection }) {
  const quality = (row.relationshipQuality ?? 'NEUTRAL') as RelationshipQuality;
  return (
    <div className="rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[13.5px] font-semibold text-[#F7F5F0]">{row.targetPlanet}</span>
        <span className={`rounded border px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.12em] ${QUALITY_CLASS[quality]}`}>
          {quality}
        </span>
      </div>
      <div className="mt-1 text-[11.5px] text-[#EEE9DF]/55">
        {ordinal(row.relativePosition)} &middot; {row.targetRashi} &middot; {row.direction}
      </div>
      <div className="mt-1 text-[11.5px] text-[#EEE9DF]/45">{QUALITY_TEXT[quality]}</div>
    </div>
  );
}

function Group({ title, note, rows }: { title: string; note: string; rows: BnnConnection[] }) {
  return (
    <div className="mt-4">
      <div className={LABEL}>{title}</div>
      <div className="mt-0.5 text-[11px] text-[#EEE9DF]/40">{note}</div>
      {rows.length === 0 ? (
        <div className="mt-2 text-[12.5px] text-[#EEE9DF]/40">No planet in this position.</div>
      ) : (
        <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((row) => <ConnectionCard key={`${row.layer}-${row.targetPlanet}`} row={row} />)}
        </div>
      )}
    </div>
  );
}

function ChainCard({ chain }: { chain: MalaShreeChain }) {
  return (
    <div className="rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
      <div className="text-[13.5px] font-semibold text-[#F7F5F0]">{chain.startingPlanet}</div>
      <div className="mt-2 overflow-x-auto">
        <div className="min-w-max font-mono text-[12px] text-[#D6BE85]">
          {chain.chain.map((planet, index) => (
            <span key={`${planet}-${index}`}>
              {planet}
              {index < chain.chain.length - 1 ? ' \u2192 ' : ''}
            </span>
          ))}
          {chain.isCycle ? ' \u21bb' : ''}
        </div>
      </div>
      <div className="mt-2 text-[11.5px] text-[#EEE9DF]/60">
        Connected planets: {chain.uniquePlanets.join(' \u00b7 ')}
      </div>
      <div className="mt-1 text-[11.5px] text-[#EEE9DF]/60">Connected count: {chain.count}</div>
      {chain.isCycle && (
        <div className="mt-1 text-[11.5px] text-[#EEE9DF]/60">
          Closed cycle: {chain.cycleArrow || chain.cycle.join(' \u2192 ')}
        </div>
      )}
    </div>
  );
}

export function BnnConnections({ data }: { data: KundliResponse }) {
  const [planet, setPlanet] = useState('Sun');
  const analysis = data.analysis;
  const bnn = analysis?.bnnConnections;
  const rows = bnn?.connections?.[planet] ?? [];
  const retro = bnn?.retrogradeLayers?.[planet];
  const node = bnn?.nodeLayers?.[planet];

  return (
    <section className={`${PANEL} p-4 sm:p-5`}>
      <div className={LABEL}>BNN Connections</div>
      <p className="mt-1 max-w-3xl text-[12px] leading-relaxed text-[#EEE9DF]/45">
        Connections are calculated by position and always exist as connections. Relationship quality is a
        separate annotation &mdash; an enemy relationship does not remove the connection.
      </p>

      <div className="mt-3 -mx-1 overflow-x-auto px-1"><div className="flex min-w-max gap-1.5">
        {PLANETS.map((option) => (
          <button
            key={option}
            onClick={() => setPlanet(option)}
            aria-pressed={planet === option}
            className={`rounded px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] transition-colors ${
              planet === option ? 'bg-[#7B1D26] text-[#F7F5F0]' : 'text-[#EEE9DF]/50 hover:text-[#D6BE85]'
            }`}
          >
            {option}
          </button>
        ))}
      </div></div>

      {node ? (
        <div className="mt-4 rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
          <div className={LABEL}>Node Position</div>
          <div className="mt-2 text-[12.5px] text-[#EEE9DF]/75">
            {planet} is in {node.nodeRashi} &middot; dispositor {node.dispositor ?? '\u2014'}
            {node.dispositorRashi ? ` in ${node.dispositorRashi}` : ''}
          </div>
          <div className="mt-1 text-[11.5px] text-[#EEE9DF]/45">
            Node analysis also considers the position of its sign lord.
          </div>
        </div>
      ) : null}

      {retro && Object.keys(retro).length > 0 ? (
        <div className="mt-4 space-y-2">
          {(['ACTUAL_POSITION', 'RETRO_PREVIOUS_POSITION'] as const).map((layer) => (
            <details key={layer} className="rounded border border-[#A62A34]/25 bg-[#0E0708]/40 p-3" open>
              <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[0.14em] text-[#B39250]">
                {LAYER_TEXT[layer]}
              </summary>
              <Group
                title={LAYER_TEXT[layer]}
                note="Connections from this reference position"
                rows={retro[layer] ?? []}
              />
            </details>
          ))}
        </div>
      ) : (
        GROUPS.map((group) => (
          <Group
            key={group.key}
            title={group.title}
            note={`${group.note} \u00b7 positions ${group.positions.join(' / ')}`}
            rows={rows.filter((row) => row.connectionGroup === group.key)}
          />
        ))
      )}

      {node ? (
        <>
          <Group title="Direct Position" note="Connections from the node's actual rashi" rows={node.direct ?? []} />
          <Group
            title="Dispositor / Operational Position"
            note={node.operationalReferenceRashi
              ? `Connections from ${node.operationalReferenceRashi}, where the dispositor sits`
              : 'Connections from the dispositor position'}
            rows={node.operational ?? []}
          />
        </>
      ) : null}

      {rows.length === 0 && !retro && !node && (
        <div className="mt-4 text-[13px] text-[#EEE9DF]/50">
          No primary BNN connection is present for this planet.
        </div>
      )}

      <div className="mt-7">
        <div className={LABEL}>Mala-Shree Connections</div>
        <p className="mt-1 text-[12px] text-[#EEE9DF]/45">
          Each chain follows the dispositor sequence. Larger connected networks indicate a more extensive
          connection. No score or prediction is derived.
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(analysis?.malaShree ?? []).map((chain) => <ChainCard key={chain.startingPlanet} chain={chain} />)}
        </div>
      </div>
    </section>
  );
}
