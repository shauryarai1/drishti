'use client';

import React, { useEffect } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { CelestialField } from './motion/CelestialField';

interface KavachIntroProps {
  onComplete: () => void;
}

const EASE = [0.22, 1, 0.36, 1] as const;
const TIMELINE_SECONDS = 3.1;

/**
 * The opening brand moment. The KAVACH wordmark resolves, holds, then the
 * environment pulls back and dissolves into the live hero that already sits
 * beneath it — so the intro reads as the page opening, not a splash fading to
 * black. The celestial field is shared visual language with the hero, which is
 * what keeps the transition continuous.
 */
export function KavachIntro({ onComplete }: KavachIntroProps) {
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
      onComplete();
      return;
    }
    // Safety net only: the primary completion signal is the overlay's own
    // animation finishing (see onAnimationComplete below).
    const timer = setTimeout(onComplete, TIMELINE_SECONDS * 1000 + 600);
    return () => clearTimeout(timer);
  }, [onComplete, reduce]);

  if (reduce) return null;

  return (
    <motion.div
      className="pointer-events-none fixed inset-0 z-[90] flex items-center justify-center overflow-hidden bg-[#090909]"
      initial={{ opacity: 1 }}
      animate={{ opacity: [1, 1, 1, 0] }}
      transition={{ duration: TIMELINE_SECONDS, times: [0, 0.62, 0.74, 1], ease: 'easeInOut' }}
      onAnimationComplete={onComplete}
      aria-hidden="true"
    >
      {/* Ambient environment + grid */}
      <div className="absolute inset-0 architectural-grid" />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute left-1/2 top-1/2 h-[60vmin] w-[60vmin] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#541219]/25 blur-[120px]" />
      </div>

      {/* Compressed orbital system that expands as the intro opens */}
      <motion.div
        className="absolute inset-0"
        initial={{ opacity: 0, scale: 0.7 }}
        animate={{ opacity: [0, 0.9, 0.9, 0], scale: [0.7, 0.84, 0.9, 1.1] }}
        transition={{ duration: TIMELINE_SECONDS, times: [0, 0.3, 0.72, 1], ease: EASE }}
      >
        <CelestialField variant="full" />
      </motion.div>

      {/* Expanding architectural seam */}
      <motion.div
        className="kavach-seam absolute left-1/2 top-1/2 h-px -translate-x-1/2 -translate-y-1/2"
        initial={{ width: 0, opacity: 0 }}
        animate={{ width: ['0px', '0px', '44vw', '130vw'], opacity: [0, 0, 0.65, 0] }}
        transition={{ duration: TIMELINE_SECONDS, times: [0, 0.5, 0.76, 1], ease: 'easeInOut' }}
      />

      {/* Centered wordmark */}
      <div className="relative z-10 text-center">
        <motion.h1
          className="font-bold text-[#F7F5F0] text-4xl sm:text-6xl md:text-7xl"
          initial={{ opacity: 0, y: 18, letterSpacing: '0.62em' }}
          animate={{
            opacity: [0, 1, 1, 0],
            y: [18, 0, 0, -10],
            letterSpacing: ['0.62em', '0.34em', '0.34em', '0.48em'],
            scale: [1, 1, 1, 1.12],
          }}
          transition={{ duration: TIMELINE_SECONDS, times: [0, 0.32, 0.66, 1], ease: EASE }}
        >
          KAVACH
        </motion.h1>

        <motion.p
          className="mt-4 font-mono text-[10px] sm:text-xs uppercase tracking-[0.42em] text-[#B39250]"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.75, 0.75, 0] }}
          transition={{ duration: TIMELINE_SECONDS, times: [0, 0.34, 0.66, 0.94] }}
        >
          Astrological Early-Warning System
        </motion.p>
      </div>
    </motion.div>
  );
}
