import React from 'react';
import { CautionPeriod } from '../lib/types';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Calendar, Clock, AlertCircle } from 'lucide-react';

interface CautionTimelineProps {
  periods: CautionPeriod[];
}

export function CautionTimeline({ periods }: CautionTimelineProps) {
  const current = periods.find((period) => period.isCurrent);
  const upcoming = periods.filter((period) => !period.isCurrent);

  return (
    <section className="relative w-full bg-[#090909] text-[#EEE9DF] py-24 sm:py-32 border-t border-[#A62A34]/20">
      <Container size="lg">
        {/* Section Header */}
        <div className="max-w-3xl mb-16 space-y-4">
          <SectionLabel label="CHRONOLOGICAL WINDOWS" number="SEC.05" tone="crimson" />

          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#F7F5F0] leading-tight">
            When should you be extra careful?
          </h2>

          <p className="text-base sm:text-lg text-[#EEE9DF]/75 leading-relaxed">
            Some periods deserve a slower pace and closer attention. Use these windows as a practical reminder to avoid unnecessary escalation and give important decisions more time.
          </p>
        </div>

        <div className="mb-14 rounded-xl border border-[#A62A34]/30 bg-[#160A0C]/70 p-6 sm:p-8">
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#B39250]">CURRENT STATUS</span>
          <p className="mt-4 text-lg font-semibold text-[#F7F5F0]">
            {current ? `A caution period is active through ${current.period.split(' — ')[1]}.` : 'No major caution period is active right now.'}
          </p>
          {current && <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/75">Move more deliberately around {current.focus.toLowerCase()} and avoid unnecessary escalation.</p>}
        </div>

        {/* Timeline Layout */}
        <div className="relative border-l border-[#A62A34]/30 ml-4 sm:ml-8 pl-8 sm:pl-12 space-y-12">
          {upcoming.map((item, index) => {
            const isCritical = item.intensity === 'critical';
            const isHeightened = item.intensity === 'heightened';

            const badgeColor = isCritical
              ? 'text-[#E53E3E] bg-[#541219]/40 border-[#E53E3E]/40'
              : isHeightened
              ? 'text-[#B39250] bg-[#B39250]/10 border-[#B39250]/30'
              : 'text-[#EEE9DF]/70 bg-[#160A0C] border-[#A62A34]/20';

            const dotColor = isCritical
              ? 'bg-[#E53E3E] ring-4 ring-[#E53E3E]/20'
              : isHeightened
              ? 'bg-[#B39250] ring-4 ring-[#B39250]/20'
              : 'bg-[#A62A34] ring-4 ring-[#A62A34]/20';

            return (
              <div key={item.id} className="relative group">
                {/* Node on the timeline */}
                <div
                  className={`absolute -left-[41px] sm:-left-[57px] top-1.5 w-4 h-4 rounded-full transition-transform duration-300 group-hover:scale-125 ${dotColor}`}
                />

                {/* Card representation of the caution period */}
                <div className="p-6 sm:p-8 rounded-xl bg-[#160A0C]/80 border border-[#A62A34]/30 hover:border-[#A62A34]/60 transition-all duration-300 shadow-xl space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-xs font-mono text-[#F7F5F0]">
                      <Calendar className="w-3.5 h-3.5 text-[#A62A34]" />
                      <span className="font-semibold text-sm sm:text-base tracking-wide">
                        {item.period}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${badgeColor}`}>
                        {item.intensity} CAUTION
                      </span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#090909] text-[#EEE9DF]/60 border border-[#A62A34]/20">
                        {item.focus}
                      </span>
                    </div>
                  </div>

                  <h3 className="text-xl sm:text-2xl font-bold text-[#F7F5F0] tracking-tight">
                    {item.title}
                  </h3>

                  <p className="text-sm sm:text-base text-[#EEE9DF]/75 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
