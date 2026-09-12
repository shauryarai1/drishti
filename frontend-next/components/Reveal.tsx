import React from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { DRISHTI_MOTION } from '../lib/tokens';

interface RevealProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  yOffset?: number;
  className?: string;
}

export function Reveal({
  children,
  delay = 0,
  duration = DRISHTI_MOTION.durations.deliberate,
  yOffset = 24,
  className = '',
}: RevealProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: yOffset }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{
        duration,
        delay,
        ease: DRISHTI_MOTION.easeOutCubic,
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
