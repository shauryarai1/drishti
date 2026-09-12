import React from 'react';
import { Check } from 'lucide-react';

interface ReadingProgressProps {
  currentStep: number; // 1, 2, or 3
  totalSteps?: number;
  onStepClick?: (step: number) => void;
}

export function ReadingProgress({
  currentStep,
  totalSteps = 3,
  onStepClick,
}: ReadingProgressProps) {
  const steps = [
    { number: 1, title: 'Date of Birth', code: 'DATE' },
    { number: 2, title: 'Time of Birth', code: 'TIME' },
    { number: 3, title: 'Place of Birth', code: 'PLACE' },
  ];

  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between relative">
        {/* Connecting line */}
        <div className="absolute top-1/2 left-4 right-4 -translate-y-1/2 h-[1px] bg-[#A62A34]/20 z-0" />

        {steps.map((step) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;
          const isUpcoming = step.number > currentStep;

          return (
            <div
              key={step.number}
              onClick={() => isCompleted && onStepClick && onStepClick(step.number)}
              className={`relative z-10 flex flex-col items-center gap-1.5 transition-all select-none ${
                isCompleted ? 'cursor-pointer' : ''
              }`}
            >
              {/* Step indicator node */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-mono text-xs font-semibold transition-all duration-300 ${
                  isCompleted
                    ? 'bg-[#7B1D26] text-[#F7F5F0] ring-2 ring-[#A62A34]'
                    : isCurrent
                    ? 'bg-[#A62A34] text-[#F7F5F0] ring-4 ring-[#7B1D26]/40 scale-110 shadow-[0_0_16px_rgba(166,42,52,0.6)]'
                    : 'bg-[#160A0C] text-[#EEE9DF]/40 border border-[#A62A34]/20'
                }`}
              >
                {isCompleted ? <Check className="w-3.5 h-3.5" /> : `0${step.number}`}
              </div>

              {/* Step title label */}
              <span
                className={`text-[11px] font-mono tracking-wider transition-colors ${
                  isCurrent
                    ? 'text-[#F7F5F0] font-semibold'
                    : isCompleted
                    ? 'text-[#EEE9DF]/70'
                    : 'text-[#EEE9DF]/30'
                }`}
              >
                {step.code}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
