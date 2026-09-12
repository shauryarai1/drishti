import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export interface MicroPanelProps {
  category: string;
  metric?: string | number;
  label: string;
  actionText?: string;
  onAction?: () => void;
  accent?: 'crimson' | 'brass' | 'scarlet';
  className?: string;
  style?: React.CSSProperties;
}

export function MicroPanel({
  category,
  metric,
  label,
  actionText,
  onAction,
  accent = 'crimson',
  className = '',
  style,
}: MicroPanelProps) {
  const accentIndicator = {
    crimson: 'bg-[#A62A34]',
    brass: 'bg-[#B39250]',
    scarlet: 'bg-[#E53E3E]',
  }[accent];

  const accentBorder = {
    crimson: 'border-[#A62A34]/30 hover:border-[#A62A34]/60',
    brass: 'border-[#B39250]/30 hover:border-[#B39250]/60',
    scarlet: 'border-[#E53E3E]/30 hover:border-[#E53E3E]/60',
  }[accent];

  return (
    <div
      style={style}
      onClick={onAction}
      className={`group relative p-3.5 sm:p-4 rounded-md bg-[#160A0C]/85 backdrop-blur-xl border transition-all duration-300 shadow-[0_8px_32px_rgba(0,0,0,0.6)] select-none ${
        onAction ? 'cursor-pointer' : ''
      } ${accentBorder} ${className}`}
    >
      {/* Top row: tiny indicator + category */}
      <div className="flex items-center justify-between gap-3 mb-1.5">
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${accentIndicator} shadow-[0_0_8px_currentColor]`} />
          <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#EEE9DF]/70 font-medium">
            {category}
          </span>
        </div>
        {actionText && (
          <ArrowUpRight className="w-3 h-3 text-[#EEE9DF]/50 group-hover:text-[#F7F5F0] transition-colors duration-200" />
        )}
      </div>

      {/* Main value or title */}
      <div className="flex items-baseline gap-2">
        {metric !== undefined && (
          <span className="font-mono text-xl sm:text-2xl font-semibold tracking-tight text-[#F7F5F0]">
            {metric}
          </span>
        )}
        <span className="text-xs sm:text-[13px] font-medium text-[#EEE9DF] tracking-wide leading-snug">
          {label}
        </span>
      </div>

      {/* Action link if provided */}
      {actionText && (
        <div className="mt-2 pt-2 border-t border-[#A62A34]/20 flex items-center justify-between text-[11px] text-[#A62A34] group-hover:text-[#F7F5F0] transition-colors">
          <span>{actionText}</span>
          <span className="opacity-60 font-mono text-[9px]">LIVE MOCK</span>
        </div>
      )}
    </div>
  );
}
