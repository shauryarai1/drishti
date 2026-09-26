import React from 'react';
import { hasNavtara, navtaraJanma, navtaraRows, planetsByNakshatra, planetsForNakshatra } from './kundliCompat';

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

export function NavtaraPanel({ data, kundli }: { data: unknown; kundli?: unknown }) {
  if (!hasNavtara(data)) {
    return (
      <section className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5">
        <div className={LABEL}>Navtara</div>
        <div className="mt-3 text-[13px] text-[#EEE9DF]/60">
          Navtara is unavailable for this saved Kundli. Generate the Kundli again to view it.
        </div>
      </section>
    );
  }

  const rows = navtaraRows(data);
  const janma = navtaraJanma(data);
  // Authoritative natal planets joined to their calculated Nakshatra.
  const planetMap = planetsByNakshatra(kundli);

  return (
    <section className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5">
      <div className={LABEL}>Navtara</div>
      <div className="mt-2 text-[13px] text-[#EEE9DF]/65">
        Janma Nakshatra: <span className="font-semibold text-[#F7F5F0]">{janma || '—'}</span>
      </div>

      <div className="mt-4 hidden grid-cols-[48px_1.1fr_0.85fr_1fr_1.1fr_1.7fr] gap-3 border-b border-[#A62A34]/25 pb-2 sm:grid">
        {['Position', 'Nakshatra', 'Tara', 'Special Role', 'Planets', 'Meaning'].map((heading) => (
          <div key={heading} className={LABEL}>{heading}</div>
        ))}
      </div>
      <div className="mt-2 space-y-2">
        {rows.map((item) => {
          const planets = planetsForNakshatra(item.nakshatra, planetMap);
          return (
            <div
              key={item.position}
              className={`grid grid-cols-[36px_1fr_auto] gap-x-3 gap-y-1 rounded border p-3 sm:grid-cols-[48px_1.1fr_0.85fr_1fr_1.1fr_1.7fr] sm:items-center sm:gap-3 ${
                item.position === 1 ? 'border-[#D6BE85]/60 bg-[#B39250]/10' : 'border-[#A62A34]/20 bg-[#0E0708]/45'
              }`}
            >
              <div className="font-mono text-[12px] font-semibold text-[#D6BE85]">{String(item.position).padStart(2, '0')}</div>
              <div className="text-[13px] font-semibold text-[#F7F5F0]">
                {item.nakshatra}
                {planets.length > 0 && (
                  <span className="mt-0.5 block text-[11px] font-normal tracking-[0.04em] text-[#D6BE85] sm:hidden">
                    {planets.join(' · ')}
                  </span>
                )}
              </div>
              <div className="text-right text-[12px] font-semibold text-[#D6BE85] sm:text-left">{item.tara}</div>
              <div className="col-span-2 text-[11px] uppercase tracking-[0.1em] text-[#B39250] sm:col-span-1">
                {item.specialRoles.length ? item.specialRoles.join(' · ') : '—'}
              </div>
              <div className="hidden text-[12px] text-[#D6BE85] sm:block">
                {planets.length ? planets.join(' · ') : '—'}
              </div>
              <div className="col-span-2 text-[12px] leading-relaxed text-[#EEE9DF]/65 sm:col-span-1">{item.meaning}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
