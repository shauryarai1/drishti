'use client';

import React from 'react';
import type { KundliResponse } from '../../lib/kundli';

// Technical chart analysis: standard aspects (kept separate from BNN), karakas,
// conditions, conjunctions and the sign/house distributions.

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70';
const CELL = 'px-3 py-2 text-left text-[12.5px] whitespace-nowrap';

function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-[#A62A34]/15 py-3">
      <div className={LABEL}>{title}</div>
      <div className="mt-1.5 text-[12.5px] leading-relaxed text-[#EEE9DF]/75">{children}</div>
    </div>
  );
}

function GroupList({ title, groups }: { title: string; groups: Record<string, string[]> }) {
  return (
    <Row title={title}>
      <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
        {Object.entries(groups).map(([name, planets]) => (
          <div key={name}>
            <span className="text-[#D6BE85]">{name}:</span>{' '}
            {planets.length > 0 ? planets.join(' \u00b7 ') : <span className="text-[#EEE9DF]/40">None</span>}
          </div>
        ))}
      </div>
    </Row>
  );
}

export function ChartAnalysis({ data }: { data: KundliResponse }) {
  const analysis = data.analysis;
  if (!analysis) {
    return (
      <section className={`${PANEL} p-4 sm:p-5`}>
        <div className={LABEL}>Chart Analysis</div>
        <div className="mt-2 text-[13px] text-[#EEE9DF]/50">Technical analysis is unavailable for this chart.</div>
      </section>
    );
  }

  const dignity = analysis.dignity ?? {};
  const combust = Object.values(analysis.strength?.planets ?? {}).filter((item) => item.combustion?.isCombust);

  return (
    <section className={`${PANEL} p-4 sm:p-5`}>
      <div className={LABEL}>Standard Planetary Aspects</div>
      <p className="mt-1 text-[12px] text-[#EEE9DF]/45">
        Traditional planetary house aspects shown separately from BNN connections.
      </p>
      <div className="mt-3 -mx-1 overflow-x-auto px-1">
        <table className="w-full min-w-[420px] border-collapse">
          <thead>
            <tr>{['Planet', 'Current House', 'Aspect', 'Aspected House'].map((heading) => (
              <th key={heading} className={`${LABEL} border-b border-[#A62A34]/25 pb-2 ${CELL}`}>{heading}</th>
            ))}</tr>
          </thead>
          <tbody>
            {(analysis.standardAspects ?? []).map((row) => (
              <tr key={row.planet}>
                <td className={`${CELL} font-semibold text-[#F7F5F0]`}>{row.planet}</td>
                <td className={CELL}>H{row.fromHouse}</td>
                <td className={CELL}>{row.offsets.join(', ')}</td>
                <td className={CELL}>{row.aspects.map((house) => `H${house}`).join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6">
        <div className={LABEL}>Chart Profile</div>
        <Row title="Lagna / Lagnesh">
          {analysis.lagna.lagnaSign} &middot; {analysis.lagna.lagnesh}
          {analysis.lagna.lagneshRashi ? ` in ${analysis.lagna.lagneshRashi}` : ''}
          {analysis.lagna.lagneshHouse ? ` (H${analysis.lagna.lagneshHouse})` : ''}
        </Row>
        <Row title="Atmakaraka">
          {analysis.atmakaraka?.atmakaraka ?? '\u2014'}
          {typeof analysis.atmakaraka?.degreeInSign === 'number'
            ? ` \u00b7 ${analysis.atmakaraka.degreeInSign.toFixed(2)}\u00b0` : ''}
        </Row>
        <Row title="Yogakaraka">
          {analysis.yogakaraka ?? 'No classical single Yogakaraka for this Lagna.'}
        </Row>
        <Row title="Maraka Lords (technical classification only)">
          H2: {analysis.maraka?.lords?.['2'] ?? '\u2014'} &middot; H7: {analysis.maraka?.lords?.['7'] ?? '\u2014'}
        </Row>
        <Row title="Badhaka">
          {analysis.badhaka?.modality ? `${analysis.badhaka.modality} ascendant` : '\u2014'} &middot; House{' '}
          {analysis.badhaka?.house ?? '\u2014'} {analysis.badhaka?.sign ? `(${analysis.badhaka.sign})` : ''} &middot; Badhakesh{' '}
          {analysis.badhaka?.lord ?? '\u2014'}
        </Row>
        <GroupList title="Planetary Conditions" groups={{
          Exalted: dignity.exalted ?? [],
          'Own sign': dignity.own_sign ?? [],
          Debilitated: dignity.debilitated ?? [],
          Other: dignity.other ?? [],
        }} />
        <Row title="Retrograde Planets">
          {(() => {
            const retro = data.planets.filter((planet) => planet.motion === 'Retrograde').map((planet) => planet.planet);
            return retro.length > 0 ? retro.join(' \u00b7 ') : <span className="text-[#EEE9DF]/40">None</span>;
          })()}
        </Row>
        <Row title="Combust Planets">
          {combust.length > 0
            ? combust.map((item) => item.referencePlanet).join(' \u00b7 ')
            : <span className="text-[#EEE9DF]/40">None</span>}
        </Row>
        <Row title="Conjunctions (same sign)">
          {(analysis.conjunctions ?? []).length > 0 ? (
            <div className="grid gap-1 sm:grid-cols-2">
              {analysis.conjunctions.map((item) => (
                <div key={`${item.planets.join('-')}-${item.rashi}`}>
                  {item.planets.join(' \u00b7 ')} <span className="text-[#EEE9DF]/45">in {item.rashi}</span>
                </div>
              ))}
            </div>
          ) : <span className="text-[#EEE9DF]/40">None</span>}
        </Row>
        <GroupList title="Movable / Fixed / Dual" groups={analysis.modalities ?? {}} />
        <GroupList title="Elements" groups={analysis.elements ?? {}} />
        <GroupList title="Dharma / Artha / Kama / Moksha" groups={analysis.purushartha ?? {}} />
      </div>
    </section>
  );
}
