'use client';

import React, { useState } from 'react';
import { Kundli } from '../Kundli';
import { birthDetailsFor, toKundliData, type KundliResponse } from '../../lib/kundli';

// Chart switcher: D1 and Moon Chart. Both payloads come from the backend; the
// Moon Chart's house transform is NOT recalculated here.

const RASHIS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const LABEL = 'font-mono text-[10px] uppercase tracking-[0.18em] text-[#B3922F]';

function moonChartToKundliData(moon: NonNullable<KundliResponse['analysis']>['moonChart']) {
  const start = RASHIS.indexOf(moon.lagnaSign);
  const byHouse = new Map<number, Array<{ planet: string; house: number; sign: string; degree: number; motion: string }>>();
  for (const [planet, data] of Object.entries(moon.placements ?? {})) {
    const list = byHouse.get(data.house) ?? [];
    const longitude = typeof data.longitude === 'number' ? data.longitude : 0;
    list.push({ planet, house: data.house, sign: data.rashi, degree: longitude % 30, motion: 'Direct' });
    byHouse.set(data.house, list);
  }
  const houses = Array.from({ length: 12 }, (_unused, index) => {
    const house = index + 1;
    return {
      number: house,
      rashi: RASHIS[(start + index) % 12],
      cuspLongitude: 0,
      planets: byHouse.get(house) ?? [],
    };
  });
  return toKundliData({
    ascendant: { rashi: moon.lagnaSign, degree: 0, longitude: 0,
      nakshatra: '', pada: 0, nakshatraLord: '' },
    houses,
    planets: [],
  });
}

export function KundliCharts({ data }: { data: KundliResponse }) {
  const [view, setView] = useState<'D1' | 'MOON'>('D1');
  const analysis = data.analysis;

  return (
    <section className="-mx-3 w-[calc(100%+1.5rem)] bg-transparent p-0 sm:mx-0 sm:w-full">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-1 sm:px-0">
        <div className="text-[15px] font-semibold tracking-[0.04em] text-[#F7F5F0]">{view === 'D1' ? 'Lagna Chart' : 'Moon Chart'}</div>
        <div className="flex gap-1.5">
          {(['D1', 'MOON'] as const).map((option) => (
            <button
              key={option}
              onClick={() => setView(option)}
              aria-pressed={view === option}
              className={`rounded px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                view === option ? 'bg-[#7B1D26] text-[#F7F5F0]' : 'text-[#EEE9DF]/50 hover:text-[#D6BE85]'
              }`}
            >
              {option === 'D1' ? 'D1 / Lagna' : 'Moon Chart'}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-1">
        {view === 'D1' ? (
          <Kundli
            kundli={toKundliData(data.chart)}
            birthDetails={birthDetailsFor(data)}
            ascendant={data.chart.ascendant.rashi}
          />
        ) : analysis?.moonChart?.lagnaSign ? (
          <>
            <Kundli
              kundli={moonChartToKundliData(analysis.moonChart)}
              birthDetails={birthDetailsFor(data)}
              ascendant={analysis.moonChart.lagnaSign}
            />
          </>
        ) : (
          <div className="text-[13px] text-[#EEE9DF]/50">Moon Chart is unavailable for this chart.</div>
        )}
      </div>

    </section>
  );
}
