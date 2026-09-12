/**
 * DRISHTI Centralized Design Tokens
 *
 * Palette: Sophisticated Red Identity with rich tonal range
 * (Near Black, Black Wine, Deep Burgundy, Crimson, Rich Red, Accent Red,
 * Warm White, Soft Ivory, Charcoal, Muted Brass)
 */

export const DRISHTI_COLORS = {
  nearBlack: '#090909',
  blackWine: '#160A0C',
  deepBurgundy: '#2B0C11',
  crimson: '#541219',
  richRed: '#7B1D26',
  accentRed: '#A62A34',
  scarletGlow: '#E53E3E',
  warmWhite: '#F7F5F0',
  softIvory: '#EEE9DF',
  pureWhite: '#FFFFFF',
  charcoal: '#171717',
  mutedBrass: '#B39250',
  paleBrass: '#D6BE85',
  borderDark: 'rgba(166, 42, 52, 0.22)',
  borderLight: 'rgba(23, 23, 23, 0.12)',
  gridLineDark: 'rgba(166, 42, 52, 0.06)',
  gridLineLight: 'rgba(23, 23, 23, 0.05)',
} as const;

export const DRISHTI_FONTS = {
  sans: 'var(--font-sans, "Plus Jakarta Sans", -apple-system, sans-serif)',
  display: 'var(--font-display, "Manrope", sans-serif)',
  serif: 'var(--font-serif, "Cinzel", Georgia, serif)',
} as const;

export const DRISHTI_MOTION = {
  easeOutCubic: [0.215, 0.61, 0.355, 1],
  easeInOutQuart: [0.76, 0, 0.24, 1],
  gentleSpring: { type: 'spring', stiffness: 120, damping: 20 },
  snappySpring: { type: 'spring', stiffness: 220, damping: 25 },
  durations: {
    micro: 0.15,
    snappy: 0.25,
    standard: 0.45,
    deliberate: 0.75,
    contemplative: 1.2,
  },
} as const;
