'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BirthDetails as BirthDetailsType } from '../../lib/types';
import { BirthDetailsFlow } from '../../components/BirthDetails';
import { LoadingExperience } from '../../components/LoadingExperience';
import { api, wakeBackend } from '../../lib/api';

const PREPARING_MESSAGE = 'Preparing your reading...';
const COLD_START_MESSAGE = 'Preparing the KAVACH engine. This may take a moment...';
const FAILURE_MESSAGE =
  "We couldn't prepare your reading right now. Your details are still here — please try again.";

export default function ReadingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [statusMessage, setStatusMessage] = useState(PREPARING_MESSAGE);
  const [error, setError] = useState('');
  const [pendingDetails, setPendingDetails] = useState<BirthDetailsType | null>(null);

  const submittingRef = useRef(false);
  const slowTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Begin waking the backend as soon as the visitor enters the reading flow.
  useEffect(() => {
    wakeBackend();
  }, []);

  useEffect(() => {
    return () => {
      if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
    };
  }, []);

  const handleComplete = async (details: BirthDetailsType) => {
    // Duplicate-submission guard: one generation flow at a time.
    if (submittingRef.current) return;

    // Public: a guest generates the reading immediately. No account is needed.
    submittingRef.current = true;

    setPendingDetails(details);
    setIsLoading(true);
    setIsReady(false);
    setError('');
    setStatusMessage(PREPARING_MESSAGE);

    if (typeof window !== 'undefined') {
      sessionStorage.setItem('drishti_birth_details', JSON.stringify(details));
    }

    if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
    slowTimerRef.current = setTimeout(() => setStatusMessage(COLD_START_MESSAGE), 6000);

    try {
      // Single controlled lifecycle. The interpretation response already contains
      // the chart, so no separate chart request is needed. Manual places without
      // coordinates are submitted as-is and resolved by the backend fallback.
      const reading = await api.getInterpretation(details);
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('drishti_reading', JSON.stringify(reading));
      }
      setIsReady(true);
    } catch {
      setError(FAILURE_MESSAGE);
    } finally {
      if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
      submittingRef.current = false;
    }
  };

  const handleRetry = () => {
    if (pendingDetails) handleComplete(pendingDetails);
  };

  const handleEditDetails = () => {
    setIsLoading(false);
    setIsReady(false);
    setError('');
  };

  const handleLoadingFinished = () => {
    router.push('/results');
  };

  const handleCancel = () => {
    router.push('/');
  };

  if (isLoading) {
    return (
      <LoadingExperience
        onFinished={handleLoadingFinished}
        isReady={isReady}
        error={error}
        statusMessage={statusMessage}
        onRetry={handleRetry}
        onEditDetails={handleEditDetails}
      />
    );
  }

  return (
    <main className="min-h-screen bg-[#090909]">
      <BirthDetailsFlow
        onComplete={handleComplete}
        onCancel={handleCancel}
        initialDetails={pendingDetails ?? undefined}
      />
    </main>
  );
}
