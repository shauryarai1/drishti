import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Container } from './Container';

interface LoadingExperienceProps {
  onFinished: () => void;
  isReady?: boolean;
  error?: string;
}

export function LoadingExperience({ onFinished, isReady = true, error }: LoadingExperienceProps) {
  const [stage, setStage] = useState<1 | 2 | 3>(1);
  const [minimumTimeElapsed, setMinimumTimeElapsed] = useState(false);

  const stages = [
    {
      id: 1,
      text: 'Preparing your chart',
      subtext: 'Calculating planetary coordinates and horizon angles...',
      code: 'HORIZON.FIX',
    },
    {
      id: 2,
      text: 'Identifying your key areas',
      subtext: 'Analyzing house placements and planetary relationships...',
      code: 'HOUSE.MAP',
    },
    {
      id: 3,
      text: 'Building your reading',
      subtext: 'Synthesizing attention, protection, and caution indicators...',
      code: 'DRISHTI.SYNTH',
    },
  ];

  useEffect(() => {
    const t1 = setTimeout(() => setStage(2), 1200);
    const t2 = setTimeout(() => setStage(3), 2600);
    const t3 = setTimeout(() => setMinimumTimeElapsed(true), 4000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  useEffect(() => {
    if (isReady && minimumTimeElapsed && !error) onFinished();
  }, [error, isReady, minimumTimeElapsed, onFinished]);

  const currentStage = stages.find((s) => s.id === stage) || stages[0];

  return (
    <div className="relative min-h-screen w-full bg-[#090909] text-[#EEE9DF] flex flex-col items-center justify-center overflow-hidden architectural-grid">
      {/* Ambient background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-[#541219]/30 blur-[120px]" />
      </div>

      <Container size="sm" className="relative z-10 text-center space-y-10">

        {/* Restrained SVG Geometric Line Construction Animation */}
        <div className="relative w-64 h-64 mx-auto flex items-center justify-center">

          {/* Subtle rotating outer frame */}
          <svg
            viewBox="0 0 200 200"
            className="w-full h-full stroke-current text-[#A62A34]"
            fill="none"
          >
            {/* Outer square boundary */}
            <motion.rect
              x="20"
              y="20"
              width="160"
              height="160"
              stroke="#A62A34"
              strokeWidth="1.2"
              strokeDasharray="640"
              initial={{ strokeDashoffset: 640 }}
              animate={{ strokeDashoffset: 0 }}
              transition={{ duration: 1.5, ease: 'easeInOut' }}
            />

            {/* Inner diamond (Lagna & Kendra core of North Indian chart) */}
            <motion.polygon
              points="100,20 180,100 100,180 20,100"
              stroke="#B39250"
              strokeWidth="1.2"
              strokeDasharray="460"
              initial={{ strokeDashoffset: 460 }}
              animate={{ strokeDashoffset: stage >= 2 ? 0 : 460 }}
              transition={{ duration: 1.2, ease: 'easeInOut' }}
            />

            {/* Corner to center diagonal division lines */}
            <motion.line
              x1="20"
              y1="20"
              x2="180"
              y2="180"
              stroke="#EEE9DF"
              strokeOpacity="0.4"
              strokeWidth="1"
              strokeDasharray="230"
              initial={{ strokeDashoffset: 230 }}
              animate={{ strokeDashoffset: stage >= 3 ? 0 : 230 }}
              transition={{ duration: 0.9, ease: 'easeOut' }}
            />
            <motion.line
              x1="180"
              y1="20"
              x2="20"
              y2="180"
              stroke="#EEE9DF"
              strokeOpacity="0.4"
              strokeWidth="1"
              strokeDasharray="230"
              initial={{ strokeDashoffset: 230 }}
              animate={{ strokeDashoffset: stage >= 3 ? 0 : 230 }}
              transition={{ duration: 0.9, ease: 'easeOut' }}
            />

            {/* Center intersection marker */}
            <motion.circle
              cx="100"
              cy="100"
              r="3"
              fill="#A62A34"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.4, duration: 0.4 }}
            />
          </svg>

          {/* Central subtle pulsing aura */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-16 h-16 rounded-full bg-[#A62A34]/15 animate-ping duration-1000" />
          </div>
        </div>

        {error && <div className="mx-auto max-w-md border border-[#A62A34]/50 bg-[#541219]/30 p-4 text-sm text-[#F7F5F0]">{error}</div>}

        {/* Text Sequence (No fake percentages) */}
        <div className="space-y-3 min-h-[90px]">
          <div className="inline-block px-2.5 py-0.5 rounded font-mono text-[10px] tracking-widest text-[#B39250] bg-[#B39250]/10 border border-[#B39250]/30">
            {currentStage.code}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStage.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="space-y-1.5"
            >
              <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                {currentStage.text}
              </h3>
              <p className="text-xs sm:text-sm font-mono text-[#EEE9DF]/60">
                {currentStage.subtext}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Subtle step dots */}
        <div className="flex items-center justify-center gap-2">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-1 rounded-full transition-all duration-300 ${
                s === stage ? 'w-8 bg-[#A62A34]' : s < stage ? 'w-2 bg-[#7B1D26]' : 'w-2 bg-[#EEE9DF]/20'
              }`}
            />
          ))}
        </div>

      </Container>
    </div>
  );
}
