import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from './Button';

interface HeaderProps {
  onStartReading: () => void;
  onNavigateSection?: (sectionId: string) => void;
  variant?: 'immersive' | 'light';
}

export function Header({
  onStartReading,
  onNavigateSection,
  variant = 'immersive',
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (sectionId: string) => {
    setMobileMenuOpen(false);
    if (onNavigateSection) {
      onNavigateSection(sectionId);
    } else {
      const el = document.getElementById(sectionId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const isLight = variant === 'light';

  return (
    <header className="relative z-40 w-full pt-6 sm:pt-8 pb-4">
      <div className="w-full max-w-7xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 flex items-center justify-between">
        {/* Brand identity */}
        <div
          onClick={() => handleNavClick('hero')}
          className="group flex items-center gap-3 cursor-pointer select-none"
        >
          {/* Subtle brass geometric marker */}
          <div className="w-2.5 h-2.5 rotate-45 border border-[#B39250] group-hover:bg-[#A62A34] transition-colors duration-300" />
          <span
            className={`text-lg sm:text-xl font-bold tracking-[0.25em] transition-colors duration-200 ${
              isLight ? 'text-[#171717]' : 'text-[#F7F5F0]'
            }`}
          >
            DRISHTI
          </span>
          <span className="hidden sm:inline-block text-[10px] uppercase font-mono tracking-widest px-2 py-0.5 border border-[#A62A34]/30 text-[#A62A34] rounded-[2px]">
            GUIDANCE
          </span>
        </div>

        {/* Center navigation links */}
        <nav className="hidden md:flex items-center gap-8 lg:gap-10">
          <button
            onClick={() => handleNavClick('how-it-works')}
            className={`text-xs uppercase tracking-[0.18em] font-medium transition-colors hover:text-[#A62A34] cursor-pointer ${
              isLight ? 'text-[#171717]/80' : 'text-[#EEE9DF]/75'
            }`}
          >
            How it works
          </button>
          <button
            onClick={() => handleNavClick('preview')}
            className={`text-xs uppercase tracking-[0.18em] font-medium transition-colors hover:text-[#A62A34] cursor-pointer ${
              isLight ? 'text-[#171717]/80' : 'text-[#EEE9DF]/75'
            }`}
          >
            The Three Areas
          </button>
          <button
            onClick={() => handleNavClick('about')}
            className={`text-xs uppercase tracking-[0.18em] font-medium transition-colors hover:text-[#A62A34] cursor-pointer ${
              isLight ? 'text-[#171717]/80' : 'text-[#EEE9DF]/75'
            }`}
          >
            About
          </button>
          <button
            onClick={() => handleNavClick('privacy')}
            className={`text-xs uppercase tracking-[0.18em] font-medium transition-colors hover:text-[#A62A34] cursor-pointer ${
              isLight ? 'text-[#171717]/80' : 'text-[#EEE9DF]/75'
            }`}
          >
            Privacy
          </button>
        </nav>

        {/* Right CTA */}
        <div className="hidden sm:flex items-center gap-4">
          <Button
            size="sm"
            variant={isLight ? 'primary' : 'primary'}
            showArrow
            onClick={onStartReading}
          >
            Begin reading
          </Button>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex sm:hidden items-center gap-2">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-[#EEE9DF] hover:text-[#FFFFFF] cursor-pointer"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden absolute top-full left-0 w-full bg-[#160A0C]/95 backdrop-blur-2xl border-b border-[#A62A34]/30 px-6 py-6 flex flex-col gap-4 shadow-2xl">
          <button
            onClick={() => handleNavClick('how-it-works')}
            className="text-left text-xs uppercase tracking-[0.2em] py-2 text-[#EEE9DF]/80 hover:text-[#F7F5F0]"
          >
            How it works
          </button>
          <button
            onClick={() => handleNavClick('preview')}
            className="text-left text-xs uppercase tracking-[0.2em] py-2 text-[#EEE9DF]/80 hover:text-[#F7F5F0]"
          >
            The Three Areas
          </button>
          <button
            onClick={() => handleNavClick('about')}
            className="text-left text-xs uppercase tracking-[0.2em] py-2 text-[#EEE9DF]/80 hover:text-[#F7F5F0]"
          >
            About
          </button>
          <button
            onClick={() => handleNavClick('privacy')}
            className="text-left text-xs uppercase tracking-[0.2em] py-2 text-[#EEE9DF]/80 hover:text-[#F7F5F0]"
          >
            Privacy
          </button>
          <div className="pt-2">
            <Button
              className="w-full"
              variant="primary"
              showArrow
              onClick={() => {
                setMobileMenuOpen(false);
                onStartReading();
              }}
            >
              Begin reading
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
