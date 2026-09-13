'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { HeroSection } from '../components/HeroSection';
import { LightEditorialSection } from '../components/LightEditorialSection';
import { ImmersiveStorySection } from '../components/ImmersiveStorySection';
import { ReadingPreviewSection } from '../components/ReadingPreviewSection';
import { Footer } from '../components/Footer';
import { wakeBackend } from '../lib/api';

export default function HomePage() {
  const router = useRouter();

  const handleStartReading = () => {
    wakeBackend();
    router.push('/reading');
  };

  const handleExploreHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF]">
      {/* 01: Viewport Hero with Midground Sculptural Centerpiece */}
      <HeroSection
        onStartReading={handleStartReading}
        onExploreHowItWorks={handleExploreHowItWorks}
      />

      {/* 02: Warm White Editorial Section */}
      <LightEditorialSection onStartReading={handleStartReading} />

      {/* 03: Organic Crimson Landscape & Synthesis Story */}
      <ImmersiveStorySection onStartReading={handleStartReading} />

      {/* 04: Editorial Triad Narrative (Attention, Protect, Danger) */}
      <ReadingPreviewSection onStartReading={handleStartReading} />

      {/* Footer */}
      <Footer onStartReading={handleStartReading} />
    </main>
  );
}
