'use client';

import React, { useRef } from 'react';
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react';
import { Header } from './Header';
import { MicroPanel } from './MicroPanel';
import { SectionLabel } from './SectionLabel';
import { CelestialField } from './motion/CelestialField';

interface HeroSectionProps {
  onStartReading: () => void;
  onExploreHowItWorks: () => void;
  onInspectMicroAttention?: () => void;
  /** True while the opening brand intro is still on screen. */
  introActive?: boolean;
}

const EASE = [0.22, 1, 0.36, 1] as const;

const TRUST_MARKERS = ['PERSONALIZED', 'SIMPLE', 'NON-FATALISTIC'];

const PRIMARY_CTA =
  'inline-flex w-full items-center justify-center rounded bg-[#7B1D26] px-8 py-4 text-base font-medium tracking-wide text-[#F7F5F0] border border-[#A62A34]/40 shadow-[0_4px_24px_rgba(123,29,38,0.35)] transition-colors hover:bg-[#A62A34] sm:w-auto';

const SECONDARY_CTA =
  'inline-flex w-full items-center justify-center rounded border border-[#B39250]/40 px-8 py-4 text-base tracking-wide text-[#F7F5F0] transition-colors hover:border-[#B39250] hover:bg-[#2B0C11]/60 sm:w-auto';

export function HeroSection({
  onStartReading,
  onExploreHowItWorks,
  onInspectMicroAttention,
  introActive = false,
}: HeroSectionProps) {
  const sectionRef = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end start'],
  });

  const deepY = useTransform(scrollYProgress, [0, 1], [0, 55]);
  const nearY = useTransform(scrollYProgress, [0, 1], [0, 120]);
  const fieldScale = useTransform(scrollYProgress, [0, 1], [1, 1.08]);
  const fieldOpacity = useTransform(scrollYProgress, [0, 0.85], [1, 0]);
  const copyY = useTransform(scrollYProgress, [0, 1], [0, -40]);

  return (
    <section
      id="hero"
      ref={sectionRef}
      className="relative min-h-screen w-full bg-[#090909] text-[#EEE9DF] flex flex-col justify-between overflow-hidden architectural-grid"
    >
      {/* ========================================================================= */}
      {/* LAYER 1: BACKGROUND (Celestial environment + architectural grid lines)     */}
      {/* ========================================================================= */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {/* Deep layer: large faint structures that drift slower than the near layer. */}
        <motion.div
          className="absolute inset-0"
          style={reduceMotion ? undefined : { y: deepY, scale: fieldScale, opacity: fieldOpacity }}
          initial={{ opacity: 0, scale: 0.86 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 2.4, delay: introActive ? 1.4 : 0, ease: EASE }}
        >
          <CelestialField variant="deep" />
        </motion.div>

        {/* Near layer: brighter midground planets, including one larger foreground body. */}
        <motion.div
          className="absolute inset-0"
          style={reduceMotion ? undefined : { y: nearY, scale: fieldScale, opacity: fieldOpacity }}
          initial={{ opacity: 0, scale: 0.78 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 2.6, delay: introActive ? 1.5 : 0, ease: EASE }}
        >
          <CelestialField variant="near" />
        </motion.div>

        {/* Readability scrim: planets passing behind the headline region recede into darkness. */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_55%_at_28%_52%,rgba(9,9,9,0.55)_0%,rgba(9,9,9,0.2)_45%,transparent_70%)] hidden lg:block" />

        {/* Deep wine & burgundy ambient radial lighting - authentic light sources */}
        <div className="absolute -top-[10%] right-[5%] w-[70vw] max-w-[900px] h-[600px] rounded-full bg-gradient-to-br from-[#7B1D26]/25 via-[#2B0C11]/30 to-transparent blur-[120px]" />
        <div className="absolute bottom-[5%] left-[10%] w-[50vw] max-w-[650px] h-[450px] rounded-full bg-gradient-to-tr from-[#541219]/20 via-[#160A0C]/40 to-transparent blur-[100px]" />

        {/* Subtle architectural vertical & horizontal boundary alignment rules */}
        <div className="absolute top-0 bottom-0 left-[10%] w-[1px] bg-[#A62A34]/10 hidden lg:block" />
        <div className="absolute top-0 bottom-0 right-[10%] w-[1px] bg-[#A62A34]/10 hidden lg:block" />
        <div className="absolute top-[28%] left-0 right-0 h-[1px] bg-[#A62A34]/10 hidden xl:block" />
        <div className="absolute bottom-[18%] left-0 right-0 h-[1px] bg-[#A62A34]/10 hidden xl:block" />
      </div>

      {/* Integrated Header */}
      <Header onStartReading={onStartReading} />

      {/* ========================================================================= */}
      {/* MAIN VIEWPORT COMPOSITION (Midground Sculptural Centerpiece + Foreground Copy) */}
      {/* ========================================================================= */}
      <motion.div
        className="relative z-10 w-full max-w-[1440px] mx-auto px-5 sm:px-8 md:px-12 lg:px-16 flex-1 flex flex-col justify-center py-10 sm:py-14 lg:py-16"
        style={reduceMotion ? undefined : { y: copyY }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          {/* ========================================== */}
          {/* LEFT / FOREGROUND: Restrained Copy & CTAs */}
          {/* ========================================== */}
          <div className="lg:col-span-5 xl:col-span-5 space-y-6 sm:space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: introActive ? 0 : 1, y: introActive ? 20 : 0 }}
              transition={{ duration: 0.75, ease: EASE }}
              className="space-y-4"
            >
              <SectionLabel label="ASTROLOGICAL GUIDANCE FOR EVERYDAY LIFE" tone="crimson" />

              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[54px] font-bold text-[#F7F5F0] tracking-tight leading-[1.14]">
                Know where to be careful.
                <br />
                <span className="text-[#EEE9DF] font-light">Know where to move forward.</span>
              </h1>
            </motion.div>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: introActive ? 0 : 1, y: introActive ? 20 : 0 }}
              transition={{ duration: 0.75, ease: EASE, delay: introActive ? 0 : 0.12 }}
              className="text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed max-w-xl font-normal"
            >
              KAVACH uses your birth details to give you simple, personalized guidance about the areas
              of life that may need your attention.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: introActive ? 0 : 1, y: introActive ? 20 : 0 }}
              transition={{ duration: 0.75, ease: EASE, delay: introActive ? 0 : 0.24 }}
              className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4"
            >
              <a href="/life-summary" className={PRIMARY_CTA}>
                EXPLORE MY LIFE
              </a>
              <a href="/ask" className={SECONDARY_CTA}>
                ASK KAVACH
              </a>
            </motion.div>

            {/* Three restrained trust markers */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: introActive ? 0 : 1, y: introActive ? 20 : 0 }}
              transition={{ duration: 0.75, ease: EASE, delay: introActive ? 0 : 0.36 }}
              className="pt-4 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-[#A62A34]/20 text-[11px] font-mono tracking-[0.16em] text-[#EEE9DF]/55"
            >
              {TRUST_MARKERS.map((marker, index) => (
                <React.Fragment key={marker}>
                  {index > 0 && <span className="text-[#B39250]/60">&bull;</span>}
                  <span>{marker}</span>
                </React.Fragment>
              ))}
            </motion.div>
          </div>

          {/* ========================================================================= */}
          {/* RIGHT / MIDGROUND: Large Organic Dimensional Centerpiece + Micro UI Units */}
          {/* ========================================================================= */}
          <div className="lg:col-span-7 xl:col-span-7 relative flex items-center justify-center min-h-[260px] sm:min-h-[440px] lg:min-h-[560px]">
            {/* Ambient backlight glow under sculpture */}
            <div className="absolute inset-4 bg-gradient-to-tr from-[#7B1D26]/30 via-[#541219]/20 to-[#B39250]/10 rounded-2xl filter blur-2xl opacity-70 pointer-events-none" />

            {/* Dimensional Art Installation Container */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.9, delay: introActive ? 1.5 : 0, ease: EASE }}
              className="relative w-full aspect-[16/10] max-h-[540px] rounded-xl overflow-hidden border border-[#A62A34]/30 shadow-[0_24px_80px_rgba(0,0,0,0.85)] group"
            >
              <img
                src="/assets/hero_sculpture.jpg"
                alt="Ruby tinted glass and ivory Kundli chart artwork"
                className="w-full h-full object-cover object-center transform transition-transform duration-1000 group-hover:scale-[1.02]"
                referrerPolicy="no-referrer"
              />

              {/* Surface reflections and dimensional rim gradient */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#090909]/90 via-transparent to-[#160A0C]/30 pointer-events-none" />
              <div className="absolute inset-0 ring-1 ring-inset ring-[#F7F5F0]/10 pointer-events-none" />

              {/* Subtle corner architectural registration markers */}
              <div className="absolute top-3 left-3 w-3 h-3 border-t border-l border-[#B39250]/60 pointer-events-none" />
              <div className="absolute top-3 right-3 w-3 h-3 border-t border-r border-[#B39250]/60 pointer-events-none" />
              <div className="absolute bottom-3 left-3 w-3 h-3 border-b border-l border-[#B39250]/60 pointer-events-none" />
              <div className="absolute bottom-3 right-3 w-3 h-3 border-b border-r border-[#B39250]/60 pointer-events-none" />
            </motion.div>

            {/* ======================================================================= */}
            {/* MICRO PRODUCT UI OVERLAYS (Floating and integrated into visual scene)    */}
            {/* ======================================================================= */}

            {/* Top-Right Micro Panel: Attention Area prompt */}
            <motion.div
              initial={{ opacity: 0, x: 20, y: -10 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              transition={{ duration: 0.7, delay: introActive ? 1.75 : 0.35, ease: EASE }}
              className="absolute -top-3 sm:top-4 right-2 sm:-right-4 w-52 sm:w-60 z-20"
            >
              <MicroPanel
                category="ATTENTION AREA"
                label="Relationships"
                actionText="A closer look →"
                accent="crimson"
                onAction={onInspectMicroAttention || onStartReading}
              />
            </motion.div>

            {/* Bottom-Left Micro Panel: Reading metric */}
            <motion.div
              initial={{ opacity: 0, x: -20, y: 15 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              transition={{ duration: 0.7, delay: introActive ? 1.85 : 0.45, ease: EASE }}
              className="absolute -bottom-4 sm:bottom-6 left-2 sm:-left-6 w-48 sm:w-56 z-20"
            >
              <MicroPanel
                category="YOUR READING"
                metric="03"
                label="areas in focus"
                accent="scarlet"
              />
            </motion.div>

            {/* Center-Right floating tag: Personal guidance */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: introActive ? 1.95 : 0.55 }}
              className="hidden sm:block absolute bottom-1/4 -right-2 sm:-right-8 z-20"
            >
              <div className="px-3.5 py-2 rounded bg-[#160A0C]/90 backdrop-blur-md border border-[#B39250]/40 shadow-xl flex items-center gap-2.5">
                <span className="w-2 h-2 rotate-45 bg-[#B39250]" />
                <div className="flex flex-col">
                  <span className="text-[9px] font-mono uppercase tracking-widest text-[#B39250]">
                    PERSONAL GUIDANCE
                  </span>
                  <span className="text-xs font-medium text-[#F7F5F0]">
                    Built around your chart
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Bottom subtle scroll-indicator bar */}
      <div className="relative z-10 w-full border-t border-[#A62A34]/15 py-3 px-6 flex items-center justify-center text-[11px] font-mono text-[#EEE9DF]/40">
        <button
          onClick={onExploreHowItWorks}
          className="flex items-center gap-2 hover:text-[#EEE9DF] transition-colors cursor-pointer"
        >
          <span>How it works</span>
          <span aria-hidden="true">&darr;</span>
        </button>
      </div>
    </section>
  );
}
