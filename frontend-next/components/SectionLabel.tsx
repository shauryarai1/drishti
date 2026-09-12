import React from 'react';

interface SectionLabelProps {
  label: string;
  number?: string;
  tone?: 'crimson' | 'brass' | 'dark' | 'muted';
  className?: string;
}

export function SectionLabel({
  label,
  number,
  tone = 'crimson',
  className = '',
}: SectionLabelProps) {
  const toneStyles = {
    crimson: {
      text: 'text-[#A62A34]',
      badge: 'border-[#A62A34]/40 bg-[#541219]/30 text-[#EEE9DF]',
      line: 'bg-[#A62A34]/40',
    },
    brass: {
      text: 'text-[#B39250]',
      badge: 'border-[#B39250]/40 bg-[#B39250]/10 text-[#D6BE85]',
      line: 'bg-[#B39250]/40',
    },
    dark: {
      text: 'text-[#171717]',
      badge: 'border-[#171717]/20 bg-[#171717]/5 text-[#171717]',
      line: 'bg-[#171717]/30',
    },
    muted: {
      text: 'text-[#EEE9DF]/70',
      badge: 'border-[#EEE9DF]/20 bg-[#EEE9DF]/5 text-[#EEE9DF]/80',
      line: 'bg-[#EEE9DF]/20',
    },
  }[tone];

  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      {number && (
        <span
          className={`px-2 py-0.5 text-[11px] font-mono font-medium tracking-wider border rounded-[3px] ${toneStyles.badge}`}
        >
          {number}
        </span>
      )}
      <span className={`text-xs uppercase tracking-[0.2em] font-semibold ${toneStyles.text}`}>
        {label}
      </span>
      <span className={`w-8 h-[1px] ${toneStyles.line}`} />
    </div>
  );
}
