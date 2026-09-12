import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        drishti: {
          black: '#090909',
          wine: '#160A0C',
          burgundy: '#2B0C11',
          crimson: '#541219',
          richRed: '#7B1D26',
          accentRed: '#A62A34',
          scarlet: '#E53E3E',
          warmWhite: '#F7F5F0',
          softIvory: '#EEE9DF',
          charcoal: '#171717',
          brass: '#B39250',
          paleBrass: '#D6BE85',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Manrope', 'sans-serif'],
        serif: ['var(--font-serif)', 'Cinzel', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
