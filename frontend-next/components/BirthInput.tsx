import React from 'react';
import { LucideIcon } from 'lucide-react';

interface BirthInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  helperText?: string;
  error?: string;
  icon?: LucideIcon;
  id: string;
}

export function BirthInput({
  label,
  helperText,
  error,
  icon: Icon,
  id,
  className = '',
  ...props
}: BirthInputProps) {
  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between">
        <label
          htmlFor={id}
          className="text-xs uppercase font-mono tracking-widest text-[#EEE9DF]/80 font-medium"
        >
          {label}
        </label>
        {helperText && !error && (
          <span className="text-[11px] font-mono text-[#EEE9DF]/40">{helperText}</span>
        )}
        {error && (
          <span className="text-[11px] font-mono text-[#E53E3E] font-medium tracking-wide">
            {error}
          </span>
        )}
      </div>

      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-4 text-[#A62A34] pointer-events-none">
            <Icon className="w-5 h-5" />
          </div>
        )}
        <input
          id={id}
          className={`w-full bg-[#160A0C] text-[#F7F5F0] text-base sm:text-lg font-mono rounded-lg px-4 py-3.5 transition-all duration-200 border outline-none ${
            Icon ? 'pl-12' : ''
          } ${
            error
              ? 'border-[#E53E3E] ring-2 ring-[#E53E3E]/20'
              : 'border-[#A62A34]/30 focus:border-[#A62A34] focus:ring-2 focus:ring-[#A62A34]/20'
          } placeholder:text-[#EEE9DF]/30 ${className}`}
          {...props}
        />
      </div>
    </div>
  );
}
