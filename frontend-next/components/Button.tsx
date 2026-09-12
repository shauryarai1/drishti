import React from 'react';
import { ArrowRight, LucideIcon } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'light' | 'ghost' | 'brass';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  showArrow?: boolean;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  showArrow = false,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  // Padding Math: horizontal padding is strictly 2x vertical padding
  const sizeStyles = {
    sm: 'py-2 px-4 text-xs tracking-wider uppercase',
    md: 'py-3 px-6 text-sm tracking-wide',
    lg: 'py-4 px-8 text-base tracking-wide',
  }[size];

  const variantStyles = {
    primary:
      'bg-[#7B1D26] hover:bg-[#A62A34] text-[#F7F5F0] border border-[#A62A34]/40 shadow-[0_4px_24px_rgba(123,29,38,0.35)] active:translate-y-[1px]',
    secondary:
      'bg-[#160A0C]/80 hover:bg-[#2B0C11] text-[#EEE9DF] border border-[#A62A34]/30 backdrop-blur-md hover:border-[#A62A34]/60 active:translate-y-[1px]',
    light:
      'bg-[#171717] hover:bg-[#2B0C11] text-[#F7F5F0] border border-[#171717] shadow-[0_4px_16px_rgba(0,0,0,0.08)] active:translate-y-[1px]',
    ghost:
      'bg-transparent hover:bg-[#541219]/20 text-[#EEE9DF] hover:text-[#FFFFFF] border border-transparent hover:border-[#A62A34]/20 active:translate-y-[1px]',
    brass:
      'bg-[#B39250]/15 hover:bg-[#B39250]/25 text-[#D6BE85] border border-[#B39250]/40 active:translate-y-[1px]',
  }[variant];

  return (
    <button
      className={`group relative inline-flex items-center justify-center gap-2.5 rounded font-medium whitespace-nowrap transition-all duration-200 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed select-none ${sizeStyles} ${variantStyles} ${className}`}
      disabled={disabled}
      {...props}
    >
      {Icon && iconPosition === 'left' && (
        <Icon className="w-4 h-4 text-current transition-transform duration-200 group-hover:-translate-x-0.5" />
      )}
      <span>{children}</span>
      {Icon && iconPosition === 'right' && (
        <Icon className="w-4 h-4 text-current transition-transform duration-200 group-hover:translate-x-0.5" />
      )}
      {showArrow && (
        <ArrowRight className="w-4 h-4 text-current transition-transform duration-200 group-hover:translate-x-1" />
      )}
    </button>
  );
}
