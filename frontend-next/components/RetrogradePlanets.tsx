import React from 'react';
import type { KundliPlanet } from '../lib/kundli';
import { retrogradePlanets } from '../lib/retrograde';

/**
 * Factual retrograde summary for a Kundli.
 *
 * Shows ONLY the bodies the authoritative KAVACH motion model classifies as
 * Retrograde. It never derives the motion itself and adds no interpretation: it
 * is plain chart information, so it renders identically for a freshly generated
 * Kundli and for one reopened from My KAVACH (both use the stored result).
 */

interface RetrogradePlanetsProps {
  planets: KundliPlanet[] | null | undefined;
  className?: string;
}

const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5';
const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

export function RetrogradePlanets({ planets, className = '' }: RetrogradePlanetsProps) {
  const retrograde = retrogradePlanets(planets);

  return (
    <section className={`${PANEL} ${className}`} aria-label="Retrograde planets">
      <div className={LABEL}>Retrograde Planets</div>
      <p className="mt-1.5 text-[13px] leading-relaxed text-[#EEE9DF]/55">
        Planets moving retrograde at the time of birth.
      </p>

      {retrograde.length === 0 ? (
        <p className="mt-4 text-[14px] text-[#EEE9DF]/70">
          No planets are retrograde in this chart.
        </p>
      ) : (
        <div className="mt-4 flex flex-wrap gap-2.5 sm:gap-3">
          {retrograde.map((planet) => (
            <div
              key={planet.planet}
              className="flex items-center gap-3 rounded border border-[#A62A34]/30 bg-[#090909]/60 px-3.5 py-2.5 sm:px-4"
            >
              <span className="text-[15px] font-semibold text-[#F7F5F0]">{planet.planet}</span>
              <span className="rounded border border-[#B39250]/40 bg-[#B39250]/10 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] text-[#D6BE85]">
                Retrograde
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
