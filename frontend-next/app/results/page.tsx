'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DrishtiReading, BirthDetails } from '../../lib/types';
import { ResultsView } from '../../components/ResultsView';
import { PersonalReadingModal } from '../../components/PersonalReadingModal';
import { ResultGate } from '../../components/ResultGate';
import { useAuth } from '../../lib/auth';

export default function ResultsPage() {
  const router = useRouter();
  const { status: authStatus } = useAuth();
  const [reading, setReading] = useState<DrishtiReading | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    let details: BirthDetails = {
      date: '1994-08-16',
      time: '07:42',
      place: 'New Delhi, India',
    };

    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('drishti_birth_details');
      if (stored) {
        try {
          details = JSON.parse(stored);
        } catch {
          // fallback
        }
      }
    }

    const storedReading = sessionStorage.getItem('drishti_reading');
    if (storedReading) {
      try {
        setReading(JSON.parse(storedReading));
        return;
      } catch {
        // Fall through to the reading flow.
      }
    }
    router.replace('/reading');
  }, []);

  if (authStatus === 'loading') {
    return (
      <div className="min-h-screen bg-[#090909] flex items-center justify-center font-mono text-xs text-[#A62A34]">
        CALIBRATING REPORT...
      </div>
    );
  }

  // The personalised result is only revealed to a signed-in visitor.
  if (authStatus !== 'signedIn') {
    return (
      <main className="min-h-screen bg-[#090909] text-[#EEE9DF]">
        <div className="mx-auto w-full max-w-2xl px-5 py-16 sm:px-8">
          <ResultGate nextPath="/results" />
        </div>
      </main>
    );
  }

  if (!reading || !reading.birthDetails) {
    return (
      <div className="min-h-screen bg-[#090909] flex items-center justify-center font-mono text-xs text-[#A62A34]">
        CALIBRATING REPORT...
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#090909]">
      <ResultsView
        reading={reading}
        onReset={() => router.push('/reading')}
        onExplorePersonalReading={() => setIsModalOpen(true)}
      />

      <PersonalReadingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        defaultPlace={reading.birthDetails.place}
      />
    </main>
  );
}
