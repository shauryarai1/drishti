'use client';

import React from 'react';
import { Container } from './Container';
import { Header } from './Header';
import { MaskedReveal } from './motion/MaskedReveal';

interface AuthShellProps {
  label: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const AUTH_INPUT =
  'w-full rounded border border-[#A62A34]/25 bg-[#0E0708]/70 px-3 py-2.5 text-[13px] text-[#F7F5F0] outline-none transition-colors placeholder:text-[#EEE9DF]/30 focus:border-[#A62A34]/60';

export const AUTH_LABEL = 'block font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';

export function AuthShell({ label, title, subtitle, children, footer }: AuthShellProps) {
  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-10 sm:py-16">
        <div className="mx-auto w-full max-w-[440px]">
          <MaskedReveal>
            <div className={AUTH_LABEL}>{label}</div>
            <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">{title}</h1>
            {subtitle && (
              <p className="mt-2 text-[13px] leading-relaxed text-[#EEE9DF]/55">{subtitle}</p>
            )}
          </MaskedReveal>

          <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 sm:p-6">
            {children}
          </div>

          {footer && <div className="mt-5 text-center text-[12px] text-[#EEE9DF]/50">{footer}</div>}
        </div>
      </Container>
    </main>
  );
}
