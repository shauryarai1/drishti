'use client';

import React, { useEffect, useLayoutEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { HeroSection } from '../components/HeroSection';
import { LightEditorialSection } from '../components/LightEditorialSection';
import { ImmersiveStorySection } from '../components/ImmersiveStorySection';
import { ReadingPreviewSection } from '../components/ReadingPreviewSection';
import { Footer } from '../components/Footer';
import { KavachIntro } from '../components/KavachIntro';
import { wakeBackend } from '../lib/api';

// Module-scoped, deliberately NOT persisted anywhere.
// It lives only as long as this JS runtime, so:
//   - a fresh load / refresh / new tab re-runs the intro
//   - client-side navigation back to "/" does not replay it
let introPlayedThisRuntime = false;

// Runs before paint on the client, degrades to useEffect on the server.
const useIsoLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

export default function HomePage() {
  const router = useRouter();
  const [introActive, setIntroActive] = useState(false);

  useIsoLayoutEffect(() => {
    if (introPlayedThisRuntime) return;
    introPlayedThisRuntime = true;

    try {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!reduce) {
        setIntroActive(true);
      }
    } catch {
      // Motion preference unavailable — skip the intro rather than risk a stuck overlay.
    }
  }, []);

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
      {introActive && <KavachIntro onComplete={() => setIntroActive(false)} />}

      {/* 01: Viewport Hero with Midground Sculptural Centerpiece */}
      <HeroSection
        onStartReading={handleStartReading}
        onExploreHowItWorks={handleExploreHowItWorks}
        introActive={introActive}
      />

      {/* 02: Dark Editorial Section */}
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
