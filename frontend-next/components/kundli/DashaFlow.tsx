'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchDashaChildren,
  type KundliDasha,
  type KundliDashaPeriod,
} from '../../lib/kundli';

const LEVELS = ['Mahadasha', 'Antardasha', 'Pratyantardasha', 'Sookshma Dasha', 'Prana Dasha'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function periodDate(value: string, fine: boolean): React.ReactNode {
  const date = value.slice(0, 10).split('-');
  const formatted = date.length === 3 ? `${date[2]} ${MONTHS[Number(date[1]) - 1]} ${date[0]}` : value;
  return fine ? <>{formatted}<br /><span className="text-[10px] text-[#EEE9DF]/55">{value.slice(11, 16)}</span></> : formatted;
}

function currentFor(dasha: KundliDasha, level: number): KundliDashaPeriod | null {
  if (level === 0) return dasha.currentMahadasha;
  if (level === 1) return dasha.currentAntardasha;
  if (level === 2) return dasha.currentPratyantardasha ?? null;
  if (level === 3) return dasha.currentSookshma ?? null;
  return dasha.currentPrana ?? null;
}

export function DashaFlow({ dasha }: { dasha: KundliDasha }) {
  const root = useMemo<KundliDashaPeriod[]>(() => dasha.mahadashas, [dasha.mahadashas]);
  const [level, setLevel] = useState(0);
  const [lists, setLists] = useState<KundliDashaPeriod[][]>([root]);
  const [trail, setTrail] = useState<KundliDashaPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);

  useEffect(() => {
    setLevel(0);
    setLists([root]);
    setTrail([]);
    setError('');
  }, [root]);

  const periods = lists[level] ?? [];
  const current = currentFor(dasha, level);
  const title = LEVELS[level];

  const open = async (period: KundliDashaPeriod) => {
    if (level >= LEVELS.length - 1 || loading) return;
    setLoading(true);
    setError('');
    try {
      const result = await fetchDashaChildren(level + 1, period);
      setTrail((previous) => [...previous.slice(0, level), period]);
      setLists((previous) => [...previous.slice(0, level + 1), result.periods]);
      setLevel(level + 1);
    } catch {
      setError('That Dasha level could not be loaded. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const goTo = (target: number) => {
    setLevel(target);
    setTrail((previous) => previous.slice(0, target));
    setError('');
  };

  return (
    <section className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#B39250]">Vimshottari Dasha</div>
          <div className="mt-2 flex flex-wrap items-center gap-1 text-[11px] text-[#EEE9DF]/55">
            {['Vimshottari', ...trail.map((period) => period.lord)].map((item, index) => (
              <React.Fragment key={`${item}-${index}`}>
                {index > 0 && <span className="px-1 text-[#B39250]">›</span>}
                <button
                  type="button"
                  onClick={() => goTo(index)}
                  className={index === level ? 'text-[#D6BE85]' : 'hover:text-[#F7F5F0]'}
                >
                  {index === 0 ? item : `${item} ${['MD', 'AD', 'PD', 'SD', 'PrD'][index - 1]}`}
                </button>
              </React.Fragment>
            ))}
          </div>
        </div>
        {dasha.currentDashaFlow && dasha.currentDashaFlow.length > 0 && (
          <button
            type="button"
            onClick={() => setShowCurrent((value) => !value)}
            className="rounded border border-[#B39250]/45 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] hover:border-[#D6BE85]"
          >
            {showCurrent ? 'Hide Current Flow' : 'View Current Dasha'}
          </button>
        )}
      </div>

      {showCurrent && (
        <div className="mt-4 rounded border border-[#A62A34]/25 bg-[#0E0708]/45 p-3">
          <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-[#B39250]">Current Dasha Flow</div>
          <div className="mt-3 grid gap-2 sm:grid-cols-5">
            {(dasha.currentDashaFlow ?? []).map((period, index) => (
              <React.Fragment key={`${period.level}-${period.lord}`}>
                {index > 0 && <div className="hidden self-center text-center text-[#B39250] sm:block">↓</div>}
                <div className="rounded border border-[#A62A34]/25 bg-[#160A0C]/65 p-2">
                  <div className="text-[10px] uppercase tracking-[0.12em] text-[#B39250]">{period.level}</div>
                  <div className="mt-1 text-[15px] font-semibold text-[#F7F5F0]">{period.lord}</div>
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-[#B39250]">{title}</div>
          {level > 0 && <div className="mt-1 text-[13px] text-[#EEE9DF]/65">{trail[level - 1]?.lord} {LEVELS[level - 1]}</div>}
        </div>
        {level > 0 && (
          <button type="button" onClick={() => goTo(level - 1)} className="text-[12px] text-[#D6BE85] hover:text-[#F7F5F0]">
            ← Back to {LEVELS[level - 1]}
          </button>
        )}
      </div>

      {error && <div className="mt-3 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12px] text-[#EEE9DF]/80">{error}</div>}
      {loading && <div className="mt-3 text-[12px] text-[#EEE9DF]/55">Loading {LEVELS[level + 1]}&hellip;</div>}

      <div className="mt-3 space-y-2">
        {periods.map((period) => {
          const isCurrent = current?.start === period.start;
          const canOpen = level < LEVELS.length - 1;
          return (
            <button
              type="button"
              key={`${period.lord}-${period.start}`}
              onClick={() => void open(period)}
              disabled={!canOpen || loading}
              className={`flex w-full items-center justify-between gap-3 rounded border p-3 text-left transition-colors ${isCurrent ? 'border-[#D6BE85]/70 bg-[#B39250]/10' : 'border-[#A62A34]/25 bg-[#0E0708]/45 hover:border-[#A62A34]/60'} disabled:cursor-default`}
            >
              <span>
                <span className="block text-[15px] font-semibold text-[#F7F5F0]">{period.lord}</span>
                <span className="mt-0.5 block text-[10px] uppercase tracking-[0.12em] text-[#B39250]">{title}</span>
              </span>
              <span className="flex items-center gap-3 text-right text-[11px] text-[#EEE9DF]/65">
                <span>{periodDate(period.start, level >= 3)} → {periodDate(period.end, level >= 3)}</span>
                {isCurrent && <span className="rounded bg-[#B39250]/20 px-1.5 py-0.5 font-mono text-[9px] uppercase text-[#D6BE85]">Current</span>}
                {canOpen && <span className="text-[17px] text-[#D6BE85]">›</span>}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
