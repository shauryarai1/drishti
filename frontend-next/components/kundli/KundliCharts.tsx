'use client';

import React from 'react';
import { Kundli } from '../Kundli';
import { birthDetailsFor, toKundliData, type KundliResponse } from '../../lib/kundli';

// Leads directly with the Lagna (D1) chart. The former second-chart selector
// was removed for presentation only; all Moon calculations remain in the engine.

export function KundliCharts({ data }: { data: KundliResponse }) {
  return (
    <section className="-mx-3 w-[calc(100%+1.5rem)] bg-transparent p-0 sm:mx-0 sm:w-full">
      <div className="mb-2 px-1 sm:px-0">
        <div className="text-[15px] font-semibold tracking-[0.04em] text-[#F7F5F0]">Lagna Chart</div>
      </div>

      <div className="mt-1">
        <Kundli
          kundli={toKundliData(data.chart)}
          birthDetails={birthDetailsFor(data)}
          ascendant={data.chart.ascendant.rashi}
        />
      </div>
    </section>
  );
}
