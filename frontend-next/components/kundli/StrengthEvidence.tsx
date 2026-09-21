'use client';

import React, { useState } from 'react';
import type { KundliResponse, StrengthEvidence } from '../../lib/kundli';

// Strength EVIDENCE only. The five-level grading rule is not approved, so no
// grade, badge, percentage or score is shown anywhere.

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70';
const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

const SURROUNDING_TEXT: Record<string, string> = {
  SUPPORTIVE_BOTH_SIDES: 'Supportive on both sides',
  PRESSURED_BOTH_SIDES: 'Pressure on both sides',
  MIXED: 'Mixed surrounding influence',
  FORWARD_ONLY: 'Forward support only',
  BACKWARD_ONLY: 'Background support only',
  EMPTY: 'No surrounding planets',
};

const DIGNITY_TEXT: Record<string, string> = {
  exalted: 'Exalted',
  own_sign: 'Own sign',
  debilitated: 'Debilitated',
  neutral: 'Neutral',
  not_assigned: 'Not assigned',
};

function Block({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
      <div className={LABEL}>{title}</div>
      {items.length === 0 ? (
        <div className="mt-2 text-[12.5px] text-[#EEE9DF]/40">{empty}</div>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {items.map((item) => (
            <li key={item} className="text-[12.5px] leading-relaxed text-[#EEE9DF]/75">&middot; {item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function networkSummary(evidence: StrengthEvidence): string[] {
  const rows: string[] = [];
  if (evidence.hasTrinalNetwork) rows.push('Trinal network present');
  if (evidence.hasForwardSupport) rows.push('Forward (2nd) support present');
  if (evidence.hasBackwardSupport) rows.push('Background (12th) support present');
  if (evidence.hasThreeElevenNetwork) rows.push('3rd / 11th network present');
  if (evidence.hasOpposition) rows.push('Opposition / completion (7th) present');
  return rows;
}

export function StrengthEvidence({ data }: { data: KundliResponse }) {
  const [planet, setPlanet] = useState('Sun');
  const report = data.analysis?.strength;
  const evidence: StrengthEvidence | undefined = report?.planets?.[planet];

  return (
    <section className={`${PANEL} p-4 sm:p-5`}>
      <div className={LABEL}>Planet Strength &mdash; Evidence</div>
      <p className="mt-1 max-w-3xl text-[12px] leading-relaxed text-[#EEE9DF]/45">
        This section shows the structural evidence behind each planet. No strength grade is displayed while
        the grading rule is not finalised.
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

      {!evidence || evidence.available === false ? (
        <div className="mt-4 text-[13px] text-[#EEE9DF]/50">No evidence is available for this planet.</div>
      ) : (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <Block title="Support" items={[...evidence.supportReasons, ...networkSummary(evidence)]} empty="No supportive evidence recorded." />
          <Block title="Pressure" items={evidence.pressureReasons} empty="No pressure evidence recorded." />
          <div className="rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
            <div className={LABEL}>Structure</div>
            <div className="mt-2 text-[12.5px] text-[#F7F5F0]">
              {evidence.isIsolated ? 'Isolated' : 'Connected'}
            </div>
            <div className="mt-1 text-[12px] text-[#EEE9DF]/60">
              Surrounding condition: {SURROUNDING_TEXT[evidence.kartariCondition] ?? evidence.kartariCondition}
            </div>
            <div className="mt-1 text-[11.5px] text-[#EEE9DF]/45">
              {evidence.isolation?.isolationLevel === 'ISOLATED'
                ? 'No meaningful connections around this planet.'
                : `${evidence.isolation?.presentStructuralPositions?.length ?? 0} surrounding position(s) and ${evidence.isolation?.presentTrinalPositions?.length ?? 0} trinal position(s) occupied.`}
            </div>
          </div>
          <div className="rounded border border-[#A62A34]/25 bg-[#0E0708]/50 p-3">
            <div className={LABEL}>Position</div>
            <div className="mt-2 text-[12.5px] text-[#EEE9DF]/75">
              Dignity: {DIGNITY_TEXT[evidence.dignity] ?? evidence.dignity}
            </div>
            <div className="mt-1 text-[12.5px] text-[#EEE9DF]/75">
              Combust: {evidence.combustion?.isCombust ? 'Yes (modifier only)' : 'No'}
            </div>
            <div className="mt-1 text-[12.5px] text-[#EEE9DF]/75">
              Retrograde layers: {evidence.retrogradeLayers ? 'Yes' : 'No'}
            </div>
            {evidence.nodeDispositorLayer && (
              <div className="mt-1 text-[12.5px] text-[#EEE9DF]/75">
                Dispositor: {evidence.nodeDispositorLayer.dispositor ?? '\u2014'}
                {evidence.nodeDispositorLayer.dispositorRashi ? ` in ${evidence.nodeDispositorLayer.dispositorRashi}` : ''}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
