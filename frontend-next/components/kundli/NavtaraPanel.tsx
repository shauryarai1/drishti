import React from 'react';
import { hasNavtara, navtaraJanma, navtaraRows } from './kundliCompat';

const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

export function NavtaraPanel({ data }: { data: unknown }) {
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

  return (
    <section className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5">
      <div className={LABEL}>Navtara</div>
      <div className="mt-2 text-[13px] text-[#EEE9DF]/65">
        Janma Nakshatra: <span className="font-semibold text-[#F7F5F0]">{janma || '—'}</span>
      </div>

      <div className="mt-4 hidden grid-cols-[48px_1.25fr_1fr_1.15fr_2fr] gap-3 border-b border-[#A62A34]/25 pb-2 sm:grid">
        {['Position', 'Nakshatra', 'Tara', 'Special Role', 'Meaning'].map((heading) => (
          <div key={heading} className={LABEL}>{heading}</div>
        ))}
      </div>
      <div className="mt-2 space-y-2">
        {rows.map((item) => (
          <div
            key={item.position}
            className={`grid grid-cols-[36px_1fr_auto] gap-x-3 gap-y-1 rounded border p-3 sm:grid-cols-[48px_1.25fr_1fr_1.15fr_2fr] sm:items-center sm:gap-3 ${
              item.position === 1 ? 'border-[#D6BE85]/60 bg-[#B39250]/10' : 'border-[#A62A34]/20 bg-[#0E0708]/45'
            }`}
          >
            <div className="font-mono text-[12px] font-semibold text-[#D6BE85]">{String(item.position).padStart(2, '0')}</div>
            <div className="text-[13px] font-semibold text-[#F7F5F0]">{item.nakshatra}</div>
            <div className="text-right text-[12px] font-semibold text-[#D6BE85] sm:text-left">{item.tara}</div>
            <div className="col-span-2 text-[11px] uppercase tracking-[0.1em] text-[#B39250] sm:col-span-1">
              {item.specialRoles.length ? item.specialRoles.join(' · ') : '—'}
            </div>
            <div className="col-span-2 text-[12px] leading-relaxed text-[#EEE9DF]/65 sm:col-span-1">{item.meaning}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
