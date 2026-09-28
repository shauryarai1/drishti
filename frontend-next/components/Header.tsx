'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';
import { AccountMenu } from './AccountMenu';

interface HeaderProps {
  onStartReading: () => void;
  onNavigateSection?: (sectionId: string) => void;
  variant?: 'immersive' | 'light';
}

const NAV_LINKS = [
  { label: 'Home', href: '/' },
  { label: 'Kundli Generator', href: '/kundli' },
  { label: 'Weekly Prediction', href: '/weekly-prediction' },
  { label: 'Life Summary', href: '/life-summary' },
  { label: 'Ask Kavach', href: '/ask' },
  { label: 'YES / NO', href: '/yes-no' },
  { label: 'Matchmaking', href: '/compatibility' },
  { label: 'Panchang', href: '/panchang' },
  { label: 'Services', href: '/services' },
];

const FADE_BASE =
  'pointer-events-none absolute inset-y-0 z-10 w-[clamp(14px,1.8vw,30px)] transition-opacity duration-200';

const ARROW_CLASS =
  'hidden h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full text-[#EEE9DF]/45 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:scale-105 hover:text-[#F7F5F0] focus-visible:scale-105 focus-visible:text-[#F7F5F0] focus-visible:outline-none md:flex';

export function Header({ onStartReading, variant = 'immersive' }: HeaderProps) {
  const pathname = usePathname();
  const railRef = useRef<HTMLElement | null>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const isLight = variant === 'light';

  const syncRail = useCallback(() => {
    const el = railRef.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(max > 4 && el.scrollLeft < max - 4);
  }, []);

  useEffect(() => {
    setReduceMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }, []);

  useEffect(() => {
    const el = railRef.current;
    if (!el) return;
    syncRail();

    const onResize = () => syncRail();
    el.addEventListener('scroll', onResize, { passive: true });
    window.addEventListener('resize', onResize);

    let observer: ResizeObserver | undefined;
    if (typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(onResize);
      observer.observe(el);
    }

    // Trackpad horizontal motion and Shift+wheel work natively; a plain vertical
    // wheel over the rail is redirected into horizontal movement only while the
    // rail can still travel, so page scrolling is never trapped.
    const onWheel = (event: WheelEvent) => {
      const max = el.scrollWidth - el.clientWidth;
      if (max <= 4) return;
      const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      if (!delta) return;
      if ((el.scrollLeft <= 0 && delta < 0) || (el.scrollLeft >= max - 1 && delta > 0)) return;
      el.scrollLeft += delta;
      event.preventDefault();
    };
    el.addEventListener('wheel', onWheel, { passive: false });

    return () => {
      el.removeEventListener('scroll', onResize);
      window.removeEventListener('resize', onResize);
      el.removeEventListener('wheel', onWheel);
      observer?.disconnect();
    };
  }, [syncRail, pathname]);

  const scrollRail = (direction: -1 | 1) => {
    const el = railRef.current;
    if (!el) return;
    el.scrollBy({
      left: direction * Math.max(el.clientWidth * 0.6, 180),
      behavior: reduceMotion ? 'auto' : 'smooth',
    });
  };

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header
      className={`sticky top-0 z-50 w-full border-b backdrop-blur-md ${
        isLight ? 'border-[#171717]/10 bg-[#F7F5F0]/85' : 'border-[#A62A34]/15 bg-[#090909]/80'
      }`}
    >
      <div className="mx-auto w-full max-w-[1560px] px-[clamp(28px,4vw,76px)]">
        <div className="flex flex-wrap items-center gap-y-3 py-4 md:flex-nowrap md:py-5">
          {/* Brand — fixed left */}
          <a href="/" className="group order-1 flex shrink-0 select-none items-center gap-3">
            <div className="h-2.5 w-2.5 rotate-45 border border-[#B39250] transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:rotate-[135deg] group-hover:bg-[#A62A34]" />
            <span
              className={`font-display text-base font-semibold tracking-[0.24em] transition-colors duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] sm:text-lg ${
                isLight ? 'text-[#171717]' : 'text-[#F7F5F0]'
              }`}
            >
              KAVACH
            </span>
          </a>

          {/* Account + CTA — fixed right (second zone on mobile, third on desktop) */}
          <div className="order-2 ml-auto flex shrink-0 items-center gap-2.5 md:order-3 md:gap-3">
            <AccountMenu />
            <Button
              size="sm"
              variant="primary"
              showArrow
              onClick={onStartReading}
              className="h-9 px-3.5 text-[10px] tracking-[0.16em] hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(166,42,52,0.4)] sm:px-4 sm:text-[11px]"
            >
              Begin reading
            </Button>
          </div>

          {/* Navigable rail — own row on mobile, center zone on desktop */}
          <div className="order-3 w-full min-w-0 md:order-2 md:ml-[clamp(32px,3.2vw,56px)] md:mr-[clamp(28px,2.8vw,48px)] md:w-auto md:flex-1">
            <div className="flex items-center">
              {canScrollLeft && (
                <button
                  type="button"
                  onClick={() => scrollRail(-1)}
                  aria-label="Scroll navigation left"
                  className={ARROW_CLASS}
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
              )}

              <div className="relative min-w-0 flex-1">
                <nav
                  ref={railRef}
                  aria-label="Primary"
                  className="flex items-center overflow-x-auto py-2 antialiased [overscroll-behavior-x:contain] [scroll-behavior:smooth] [scrollbar-width:none] motion-reduce:[scroll-behavior:auto] [&::-webkit-scrollbar]:hidden"
                  style={{ gap: 'clamp(28px,2.8vw,48px)' }}
                >
                  {NAV_LINKS.map((link) => {
                    const active = isActive(link.href);
                    return (
                      <a
                        key={link.href}
                        href={link.href}
                        aria-current={active ? 'page' : undefined}
                        className={`group relative shrink-0 whitespace-nowrap px-0.5 pb-2.5 pt-1.5 font-display text-[11px] font-semibold uppercase tracking-[0.16em] transition-[color,transform] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-px focus-visible:-translate-y-px focus-visible:outline-none md:text-xs ${
                          isLight
                            ? active
                              ? 'text-[#171717]'
                              : 'text-[#171717]/70 hover:text-[#171717]'
                            : active
                              ? 'text-[#F7F5F0]'
                              : 'text-[#EEE9DF]/65 hover:text-[#F7F5F0]'
                        }`}
                      >
                        {link.label}
                        <span
                          aria-hidden
                          className={`absolute inset-x-0 bottom-0 h-[2px] origin-left rounded-full bg-[#A62A34] transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-focus-visible:scale-x-100 ${
                            active ? 'scale-x-100 opacity-100' : 'scale-x-0 opacity-0 group-hover:scale-x-100 group-hover:opacity-70'
                          }`}
                        />
                      </a>
                    );
                  })}
                </nav>

                {/* Edge fades — decorative only, never intercept clicks */}
                <span
                  aria-hidden
                  className={`${FADE_BASE} left-0 ${canScrollLeft ? 'opacity-100' : 'opacity-0'}`}
                  style={{
                    background: isLight
                      ? 'linear-gradient(to right, rgba(247,245,240,0.95), rgba(247,245,240,0))'
                      : 'linear-gradient(to right, rgba(9,9,9,0.92), rgba(9,9,9,0))',
                  }}
                />
                <span
                  aria-hidden
                  className={`${FADE_BASE} right-0 ${canScrollRight ? 'opacity-100' : 'opacity-0'}`}
                  style={{
                    background: isLight
                      ? 'linear-gradient(to left, rgba(247,245,240,0.95), rgba(247,245,240,0))'
                      : 'linear-gradient(to left, rgba(9,9,9,0.92), rgba(9,9,9,0))',
                  }}
                />
              </div>

              {canScrollRight && (
                <button
                  type="button"
                  onClick={() => scrollRail(1)}
                  aria-label="Scroll navigation right"
                  className={ARROW_CLASS}
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
