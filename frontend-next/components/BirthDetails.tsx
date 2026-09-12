import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Calendar, Clock, MapPin, ArrowLeft, ArrowRight, Search, CheckCircle2 } from 'lucide-react';
import { BirthDetails as BirthDetailsType, PlaceSuggestion } from '../lib/types';
import { api } from '../lib/api';
import { Button } from './Button';
import { BirthInput } from './BirthInput';
import { ReadingProgress } from './ReadingProgress';
import { SectionLabel } from './SectionLabel';

interface BirthDetailsFlowProps {
  onComplete: (details: BirthDetailsType) => void;
  onCancel: () => void;
  initialDetails?: Partial<BirthDetailsType>;
}

export function BirthDetailsFlow({
  onComplete,
  onCancel,
  initialDetails,
}: BirthDetailsFlowProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [date, setDate] = useState(initialDetails?.date || '');
  const [time, setTime] = useState(initialDetails?.time || '');
  const [place, setPlace] = useState(initialDetails?.place || '');

  // Place autocomplete state
  const [placeQuery, setPlaceQuery] = useState(place);
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isSearchingPlaces, setIsSearchingPlaces] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Errors
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  // Search places when query changes in Step 3
  useEffect(() => {
    if (step === 3 && placeQuery.trim().length > 1) {
      setIsSearchingPlaces(true);
      const timer = setTimeout(async () => {
        const results = await api.searchPlaces(placeQuery);
        setSuggestions(results);
        setIsSearchingPlaces(false);
      }, 150);
      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
      setIsSearchingPlaces(false);
    }
  }, [placeQuery, step]);

  const validateStep = (currentStep: number): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (currentStep === 1) {
      if (!date) {
        newErrors.date = 'Please enter your date of birth';
      } else {
        const year = parseInt(date.split('-')[0], 10);
        if (isNaN(year) || year < 1920 || year > new Date().getFullYear()) {
          newErrors.date = 'Please enter a valid birth year';
        }
      }
    }

    if (currentStep === 2) {
      if (!time) {
        newErrors.time = 'Please enter approximate time of birth';
      }
    }

    if (currentStep === 3) {
      if (!place || place.trim().length < 2) {
        newErrors.place = 'Please select or enter your birth city';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleContinue = () => {
    if (!validateStep(step)) return;

    if (step < 3) {
      setStep((prev) => (prev + 1) as 1 | 2 | 3);
    } else {
      onComplete({
        date,
        time,
        place,
      });
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((prev) => (prev - 1) as 1 | 2 | 3);
    } else {
      onCancel();
    }
  };

  // Keyboard navigation: Enter submits step
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleContinue();
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-[#090909] text-[#EEE9DF] flex flex-col justify-between architectural-grid">
      {/* Top Header bar inside flow */}
      <div className="relative z-20 w-full border-b border-[#A62A34]/20 py-4 px-6 sm:px-12 flex items-center justify-between bg-[#160A0C]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rotate-45 border border-[#B39250] bg-[#7B1D26]" />
          <span className="text-base sm:text-lg font-bold tracking-[0.25em] text-[#F7F5F0]">
            DRISHTI
          </span>
          <span className="text-[10px] font-mono tracking-widest text-[#EEE9DF]/40 pl-2 border-l border-[#A62A34]/30 hidden sm:inline">
            ASTRONOMICAL CALIBRATION
          </span>
        </div>

        <button
          onClick={onCancel}
          className="text-xs uppercase font-mono tracking-widest text-[#EEE9DF]/60 hover:text-[#F7F5F0] transition-colors cursor-pointer"
        >
          Exit to Home
        </button>
      </div>

      {/* Main split viewport */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 flex-1 py-8 sm:py-12 flex items-center">
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-center">

          {/* LEFT SIDE: Visual Environment that evolves with each step */}
          <div className="hidden lg:block lg:col-span-5 space-y-6">
            <div className="p-8 rounded-xl bg-gradient-to-br from-[#160A0C] via-[#2B0C11]/60 to-[#090909] border border-[#A62A34]/30 shadow-2xl relative overflow-hidden">

              {/* Evolving ambient glow */}
              <div
                className={`absolute -top-10 -right-10 w-64 h-64 rounded-full transition-all duration-700 blur-[80px] pointer-events-none ${
                  step === 1
                    ? 'bg-[#7B1D26]/30'
                    : step === 2
                    ? 'bg-[#B39250]/20'
                    : 'bg-[#E53E3E]/25'
                }`}
              />

              <div className="relative z-10 space-y-5">
                <SectionLabel
                  label={step === 1 ? 'STEP 01' : step === 2 ? 'STEP 02' : 'STEP 03'}
                  tone="crimson"
                />

                <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                  {step === 1 && 'The Solar & Lunar Day'}
                  {step === 2 && 'The Ascendant Horizon'}
                  {step === 3 && 'Geographical Alignment'}
                </h3>

                <p className="text-sm text-[#EEE9DF]/75 leading-relaxed">
                  {step === 1 &&
                    'Your date of birth fixes the positions of the major celestial bodies within the zodiacal circle.'}
                  {step === 2 &&
                    'Your birth time determines the rising sign (Lagna) on the eastern horizon, establishing the 12 houses.'}
                  {step === 3 &&
                    'Latitude and longitude correct for local mean time and geographical parallax, giving exact chart precision.'}
                </p>

                {/* Micro preview of entered parameters */}
                <div className="pt-4 border-t border-[#A62A34]/20 space-y-2 font-mono text-xs text-[#EEE9DF]/70">
                  <div className="flex justify-between">
                    <span className="text-[#EEE9DF]/40">DATE:</span>
                    <span className="text-[#F7F5F0]">{date || 'Pending'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#EEE9DF]/40">TIME:</span>
                    <span className="text-[#F7F5F0]">{step >= 2 ? time : 'Pending'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#EEE9DF]/40">PLACE:</span>
                    <span className="text-[#F7F5F0]">{step === 3 ? place : 'Pending'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT SIDE: Clean Functional Input Area */}
          <div className="lg:col-span-7 bg-[#160A0C]/90 backdrop-blur-2xl p-6 sm:p-10 rounded-xl border border-[#A62A34]/30 shadow-2xl space-y-8" onKeyDown={handleKeyDown}>

            {/* Progress Component */}
            <ReadingProgress currentStep={step} onStepClick={(s) => s < step && setStep(s as 1 | 2 | 3)} />

            {/* Dynamic Step Content with Transitions */}
            <AnimatePresence mode="wait">
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="space-y-2">
                    <span className="text-xs uppercase font-mono tracking-widest text-[#A62A34]">
                      Phase 01 // Solar Alignment
                    </span>
                    <h2 className="text-2xl sm:text-3xl font-bold text-[#F7F5F0]">
                      What is your date of birth?
                    </h2>
                    <p className="text-sm text-[#EEE9DF]/70">
                      Standard Gregorian calendar format (Day, Month, Year).
                    </p>
                  </div>

                  <BirthInput
                    id="dob-input"
                    label="Date of Birth"
                    type="date"
                    icon={Calendar}
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    error={errors.date}
                    autoFocus
                  />

                </motion.div>
              )}

              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="space-y-2">
                    <span className="text-xs uppercase font-mono tracking-widest text-[#B39250]">
                      Phase 02 // Ascendant Fix
                    </span>
                    <h2 className="text-2xl sm:text-3xl font-bold text-[#F7F5F0]">
                      What time were you born?
                    </h2>
                    <p className="text-sm text-[#EEE9DF]/70">
                      Even an approximate time allows us to determine the rising horizon.
                    </p>
                  </div>

                  <BirthInput
                    id="tob-input"
                    label="Time of Birth (24h or local time)"
                    type="time"
                    icon={Clock}
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    error={errors.time}
                    autoFocus
                  />

                  {/* Clarification prompt */}
                  <div className="p-3.5 rounded bg-[#090909] border border-[#A62A34]/20 flex items-start gap-3 text-xs text-[#EEE9DF]/70">
                    <CheckCircle2 className="w-4 h-4 text-[#B39250] shrink-0 mt-0.5" />
                    <span>
                      If you only know the approximate time within 30 minutes, this is sufficient to locate your primary houses.
                    </span>
                  </div>
                </motion.div>
              )}

              {step === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="space-y-2">
                    <span className="text-xs uppercase font-mono tracking-widest text-[#E53E3E]">
                      Phase 03 // Spatial Coordinates
                    </span>
                    <h2 className="text-2xl sm:text-3xl font-bold text-[#F7F5F0]">
                      Where were you born?
                    </h2>
                    <p className="text-sm text-[#EEE9DF]/70">
                      City or town. This calibrates local sunrise and astrological offsets.
                    </p>
                  </div>

                  <div className="relative">
                    <BirthInput
                      id="pob-input"
                      label="Birth City or Region"
                      icon={MapPin}
                      value={placeQuery}
                      onChange={(e) => {
                        setPlaceQuery(e.target.value);
                        setPlace(e.target.value);
                        setShowSuggestions(true);
                      }}
                      onFocus={() => setShowSuggestions(true)}
                      placeholder="e.g. New Delhi, Mumbai, London"
                      error={errors.place}
                      autoFocus
                    />

                    {/* Suggestions dropdown */}
                    {showSuggestions && suggestions.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-2 bg-[#160A0C] border border-[#A62A34]/40 rounded-lg shadow-2xl z-30 max-h-60 overflow-y-auto">
                        {suggestions.map((s) => (
                          <div
                            key={s.id}
                            onClick={() => {
                              const full = `${s.name}, ${s.region}, ${s.country}`;
                              setPlace(full);
                              setPlaceQuery(full);
                              setShowSuggestions(false);
                            }}
                            className="p-3.5 hover:bg-[#2B0C11] cursor-pointer border-b border-[#A62A34]/15 flex items-center justify-between text-sm text-[#EEE9DF]"
                          >
                            <span className="font-medium text-[#F7F5F0]">{s.name}</span>
                            <span className="text-xs font-mono text-[#EEE9DF]/50">
                              {s.region}, {s.country}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Navigation Buttons: Back and Continue */}
            <div className="pt-6 border-t border-[#A62A34]/20 flex items-center justify-between gap-4">
              <Button
                variant="ghost"
                onClick={handleBack}
                icon={ArrowLeft}
                iconPosition="left"
              >
                {step === 1 ? 'Cancel' : 'Back'}
              </Button>

              <Button
                variant="primary"
                onClick={handleContinue}
                showArrow
              >
                {step === 3 ? 'Generate My Reading' : 'Continue'}
              </Button>
            </div>

          </div>

        </div>
      </div>

      {/* Bottom informational bar */}
      <div className="relative z-10 w-full border-t border-[#A62A34]/15 py-3 px-6 text-center text-xs font-mono text-[#EEE9DF]/40">
        DATA IS ENCRYPTED IN TRANSIT &bull; ZERO PERMANENT STORAGE WITHOUT CONSENT
      </div>
    </div>
  );
}
