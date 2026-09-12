'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { BirthDetails as BirthDetailsType } from '../../lib/types';
import { BirthDetailsFlow } from '../../components/BirthDetails';
import { LoadingExperience } from '../../components/LoadingExperience';
import { api } from '../../lib/api';

export default function ReadingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState('');

  const handleComplete = (details: BirthDetailsType) => {
    setIsLoading(true);
    setIsReady(false);
    setError('');
    // In Next.js client, store temporarily in sessionStorage or URL params
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('drishti_birth_details', JSON.stringify(details));
      Promise.all([api.calculateChart(details), api.getInterpretation(details)])
        .then(([, reading]) => {
          sessionStorage.setItem('drishti_reading', JSON.stringify(reading));
          setIsReady(true);
        })
        .catch((cause) => setError(cause instanceof Error ? cause.message : 'We could not complete your reading.'));
    }
  };

  const handleLoadingFinished = () => {
    router.push('/results');
  };

  const handleCancel = () => {
    router.push('/');
  };

  if (isLoading) {
    return <LoadingExperience onFinished={handleLoadingFinished} isReady={isReady} error={error} />;
  }

  return (
    <main className="min-h-screen bg-[#090909]">
      <BirthDetailsFlow onComplete={handleComplete} onCancel={handleCancel} />
    </main>
  );
}
