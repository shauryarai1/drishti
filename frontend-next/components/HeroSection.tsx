import React from 'react';
import { motion } from 'motion/react';
import { Header } from './Header';
import { Button } from './Button';
import { MicroPanel } from './MicroPanel';
import { SectionLabel } from './SectionLabel';

interface HeroSectionProps {
  onStartReading: () => void;
  onExploreHowItWorks: () => void;
  onInspectMicroAttention?: () => void;
}

export function HeroSection({
  onStartReading,
  onExploreHowItWorks,
  onInspectMicroAttention,
}: HeroSectionProps) {
  return (
    <section
      id="hero"
      className="relative min-h-screen w-full bg-[#090909] text-[#EEE9DF] flex flex-col justify-between overflow-hidden architectural-grid"
    >
      {/* ========================================================================= */}
      {/* LAYER 1: BACKGROUND (Deep environmental texture + architectural grid lines) */}
      {/* ========================================================================= */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {/* Deep wine & burgundy ambient radial lighting - authentic light sources */}
        <div className="absolute -top-[10%] right-[5%] w-[70vw] max-w-[900px] h-[600px] rounded-full bg-gradient-to-br from-[#7B1D26]/25 via-[#2B0C11]/30 to-transparent blur-[120px]" />
        <div className="absolute bottom-[5%] left-[10%] w-[50vw] max-w-[650px] h-[450px] rounded-full bg-gradient-to-tr from-[#541219]/20 via-[#160A0C]/40 to-transparent blur-[100px]" />

        {/* Subtle architectural vertical & horizontal boundary alignment rules */}
        <div className="absolute top-0 bottom-0 left-[10%] w-[1px] bg-[#A62A34]/10 hidden lg:block" />
        <div className="absolute top-0 bottom-0 right-[10%] w-[1px] bg-[#A62A34]/10 hidden lg:block" />
        <div className="absolute top-[28%] left-0 right-0 h-[1px] bg-[#A62A34]/10 hidden xl:block" />
        <div className="absolute bottom-[18%] left-0 right-0 h-[1px] bg-[#A62A34]/10 hidden xl:block" />

        {/* Fine coordinate markers in corners */}
        <div className="absolute top-6 left-6 font-mono text-[9px] text-[#A62A34]/40 tracking-widest hidden sm:block">
          SEC.01 // LAT:28.61 // TIME:SYS
        </div>
        <div className="absolute top-6 right-6 font-mono text-[9px] text-[#A62A34]/40 tracking-widest hidden sm:block">
          REF:KUNDLI.GEOM.3D
        </div>
      </div>

      {/* Integrated Header */}
      <Header onStartReading={onStartReading} />

      {/* ========================================================================= */}
      {/* MAIN VIEWPORT COMPOSITION (Midground Sculptural Centerpiece + Foreground Copy) */}
      {/* ========================================================================= */}
      <div className="relative z-10 w-full max-w-[1440px] mx-auto px-5 sm:px-8 md:px-12 lg:px-16 flex-1 flex flex-col justify-center py-6 sm:py-12 lg:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* ========================================== */}
          {/* LEFT / FOREGROUND: Restrained Copy & CTAs */}
          {/* ========================================== */}
          <div className="lg:col-span-5 xl:col-span-5 space-y-6 sm:space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.215, 0.61, 0.355, 1] }}
              className="space-y-4"
            >
              <SectionLabel label="PERSONAL GUIDANCE" tone="crimson" />

              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[54px] font-bold text-[#F7F5F0] tracking-tight leading-[1.12]">
                Know what deserves
                <br />
                <span className="text-[#EEE9DF] font-light">your attention.</span>
              </h1>
            </motion.div>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15, ease: [0.215, 0.61, 0.355, 1] }}
              className="text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed max-w-xl font-normal"
            >
              A personalized reading built from your birth details, revealing the areas of life
              that may deserve greater awareness and care.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.28, ease: [0.215, 0.61, 0.355, 1] }}
              className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6"
            >
              <Button
                size="lg"
                variant="primary"
                showArrow
                onClick={onStartReading}
                className="w-full sm:w-auto"
              >
                Begin your reading
              </Button>

              <button
                onClick={onExploreHowItWorks}
                className="group inline-flex items-center justify-center gap-2 text-sm uppercase tracking-widest text-[#EEE9DF]/80 hover:text-[#F7F5F0] transition-colors py-3 px-2 cursor-pointer"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#B39250] group-hover:scale-125 transition-transform" />
                <span>How it works</span>
              </button>
            </motion.div>

            {/* Micro credibility indicator */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="pt-4 flex items-center gap-6 border-t border-[#A62A34]/20 text-xs font-mono text-[#EEE9DF]/50"
            >
              <div className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-[#A62A34]" />
                <span>NON-FATALISTIC</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-[#B39250]" />
                <span>3 DIMENSIONS OF CARE</span>
              </div>
            </motion.div>
          </div>

          {/* ========================================================================= */}
          {/* RIGHT / MIDGROUND: Large Organic Dimensional Centerpiece + Micro UI Units */}
          {/* ========================================================================= */}
          <div className="lg:col-span-7 xl:col-span-7 relative flex items-center justify-center min-h-[380px] sm:min-h-[460px] lg:min-h-[560px]">
            {/* Ambient backlight glow under sculpture */}
            <div className="absolute inset-4 bg-gradient-to-tr from-[#7B1D26]/30 via-[#541219]/20 to-[#B39250]/10 rounded-2xl filter blur-2xl opacity-70 pointer-events-none" />

            {/* Dimensional Art Installation Container */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.9, ease: [0.215, 0.61, 0.355, 1] }}
              className="relative w-full aspect-[16/10] max-h-[540px] rounded-xl overflow-hidden border border-[#A62A34]/30 shadow-[0_24px_80px_rgba(0,0,0,0.85)] group"
            >
              {/* Genuine bespoke visual artwork */}
              <img
                src="/assets/hero_sculpture.jpg"
                alt="Dimensional Kundli chart art installation in ruby tinted glass and ivory vellum"
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

              {/* Micro-inscription at base of visual */}
              <div className="absolute bottom-3.5 left-4 right-4 flex items-center justify-between pointer-events-none">
                <span className="text-[10px] font-mono tracking-widest text-[#EEE9DF]/60 bg-[#090909]/80 backdrop-blur-sm px-2 py-0.5 rounded-[2px] border border-[#A62A34]/20">
                  FIG. 01 // KUNDLI CARTOGRAPHY INSTALLATION
                </span>
                <span className="text-[10px] font-mono text-[#B39250]/80">
                  NORTH INDIAN GEOMETRY
                </span>
              </div>
            </motion.div>

            {/* ======================================================================= */}
            {/* MICRO PRODUCT UI OVERLAYS (Floating and integrated into visual scene)    */}
            {/* ======================================================================= */}

            {/* Top-Right Micro Panel: Attention Area prompt */}
            <motion.div
              initial={{ opacity: 0, x: 20, y: -10 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              transition={{ duration: 0.7, delay: 0.35, ease: [0.215, 0.61, 0.355, 1] }}
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
              transition={{ duration: 0.7, delay: 0.45, ease: [0.215, 0.61, 0.355, 1] }}
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
              transition={{ duration: 0.6, delay: 0.55 }}
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
      </div>

      {/* Bottom subtle scroll-indicator bar */}
      <div className="relative z-10 w-full border-t border-[#A62A34]/15 py-3 px-6 flex items-center justify-between text-[11px] font-mono text-[#EEE9DF]/40">
        <div className="flex items-center gap-3">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#A62A34] animate-pulse" />
          <span>DRISHTI ENGINE // READY</span>
        </div>
        <button
          onClick={onExploreHowItWorks}
          className="flex items-center gap-2 hover:text-[#EEE9DF] transition-colors cursor-pointer"
        >
          <span>EXPLORE THE ARCHITECTURE</span>
          <span>↓</span>
        </button>
      </div>
    </section>
  );
}
