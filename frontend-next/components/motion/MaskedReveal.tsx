'use client';

import React from 'react';
import { motion, useReducedMotion } from 'motion/react';

interface MaskedRevealProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  y?: number;
  className?: string;
  /** Optional inner className applied to the animated element. */
  innerClassName?: string;
}

const EASE = [0.22, 1, 0.36, 1] as const;

/**
 * Editorial masked reveal: content is uncovered from beneath a clipping edge
 * while easing upward. Uses transform + opacity only.
 */
export function MaskedReveal({
  children,
  delay = 0,
  duration = 0.9,
  y = 30,
  className = '',
  innerClassName = '',
}: MaskedRevealProps) {
  const reduce = useReducedMotion();

  if (reduce) {
    return <div className={`bg-transparent ${className}`}>{children}</div>;
  }

  return (
    <div className={`overflow-hidden bg-transparent ${className}`}>
      <motion.div
        initial={{ opacity: 0, y }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-12% 0px -12% 0px' }}
        transition={{ duration, delay, ease: EASE }}
        className={innerClassName}
      >
        {children}
      </motion.div>
    </div>
  );
}

interface RevealSequenceProps {
  children: React.ReactNode;
  className?: string;
  /** Stagger between direct children. */
  stagger?: number;
  delay?: number;
}

/**
 * Wraps children and reveals them in a controlled stagger when scrolled into
 * view. Children are plain elements; the parent drives the timing.
 */
export function RevealSequence({ children, className = '', stagger = 0.12, delay = 0.05 }: RevealSequenceProps) {
  const reduce = useReducedMotion();

  if (reduce) {
    return <div className={`bg-transparent ${className}`}>{children}</div>;
  }

  return (
    <motion.div
      className={`bg-transparent ${className}`}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: '-10% 0px -10% 0px' }}
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: stagger, delayChildren: delay } },
      }}
    >
      {children}
    </motion.div>
  );
}

export const revealItemVariants = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.85, ease: EASE } },
} as const;
