'use client';

import React, { useId } from 'react';

/**
 * Decorative celestial/orbital environment.
 *
 * Pure visual language: dimensional celestial bodies orbiting on thin, fading
 * paths. It deliberately does NOT depict a literal solar system, label bodies,
 * or explain the KAVACH astrology method. Motion is driven entirely by CSS
 * transforms so there are no per-frame React re-renders.
 */

type BodyTone = 'burgundy' | 'crimson' | 'stone' | 'gold';

interface CelestialBody {
  size: number;       // px diameter
  tone: BodyTone;
  opacity: number;
}

interface Orbit {
  tier: 'deep' | 'near';
  size: number;       // percentage of the field square
  duration: number;   // seconds per revolution
  offset: number;     // starting angle (deg) so bodies disperse, including when static
  reverse: boolean;
  squash: number;     // subtle ellipse depth
  strokeColor: string;
  strokeOpacity: number;
  bodies: CelestialBody[];
}

const TONES: Record<BodyTone, { surface: string; glow: string }> = {
  burgundy: {
    surface:
      'radial-gradient(circle at 32% 28%, #C06A55 0%, #7B1D26 32%, #2B0C11 68%, #0B0506 100%)',
    glow: 'rgba(166, 42, 52, 0.34)',
  },
  crimson: {
    surface:
      'radial-gradient(circle at 32% 28%, #E77A64 0%, #A62A34 36%, #541219 70%, #0B0506 100%)',
    glow: 'rgba(229, 62, 62, 0.34)',
  },
  stone: {
    surface:
      'radial-gradient(circle at 32% 28%, #FBF7EF 0%, #D8CBB8 28%, #8A7862 64%, #140D0A 100%)',
    glow: 'rgba(238, 233, 223, 0.24)',
  },
  gold: {
    surface:
      'radial-gradient(circle at 32% 28%, #F6E7BC 0%, #C9A55C 32%, #6B5327 68%, #140D0A 100%)',
    glow: 'rgba(179, 146, 80, 0.32)',
  },
};

// Deep tier: large faint structures, small distant bodies.
// Near tier: brighter midground planets, including one larger foreground body.
const ORBITS: Orbit[] = [
  {
    tier: 'deep',
    size: 96,
    duration: 64,
    offset: 0,
    reverse: false,
    squash: 0.88,
    strokeColor: '#A62A34',
    strokeOpacity: 0.34,
    bodies: [{ size: 12, tone: 'stone', opacity: 0.62 }],
  },
  {
    tier: 'deep',
    size: 82,
    duration: 52,
    offset: 55,
    reverse: true,
    squash: 0.94,
    strokeColor: '#B39250',
    strokeOpacity: 0.26,
    bodies: [{ size: 16, tone: 'burgundy', opacity: 0.66 }],
  },
  {
    tier: 'deep',
    size: 68,
    duration: 42,
    offset: 130,
    reverse: false,
    squash: 0.8,
    strokeColor: '#A62A34',
    strokeOpacity: 0.3,
    bodies: [{ size: 9, tone: 'stone', opacity: 0.6 }],
  },
  {
    tier: 'near',
    size: 54,
    duration: 34,
    offset: 200,
    reverse: true,
    squash: 0.98,
    strokeColor: '#A62A34',
    strokeOpacity: 0.42,
    bodies: [
      { size: 24, tone: 'burgundy', opacity: 0.95 },
      { size: 8, tone: 'crimson', opacity: 0.8 },
    ],
  },
  {
    tier: 'near',
    size: 40,
    duration: 27,
    offset: 265,
    reverse: false,
    squash: 0.97,
    strokeColor: '#B39250',
    strokeOpacity: 0.34,
    bodies: [{ size: 13, tone: 'stone', opacity: 0.9 }],
  },
  {
    tier: 'near',
    size: 27,
    duration: 21,
    offset: 320,
    reverse: true,
    squash: 0.96,
    strokeColor: '#A62A34',
    strokeOpacity: 0.4,
    bodies: [
      { size: 10, tone: 'gold', opacity: 0.9 },
      { size: 6, tone: 'crimson', opacity: 0.85 },
    ],
  },
];

interface CelestialFieldProps {
  className?: string;
  /** 'deep' and 'near' render split layers for parallax; 'full' renders both. */
  variant?: 'full' | 'deep' | 'near';
}

export function CelestialField({ className = '', variant = 'full' }: CelestialFieldProps) {
  // Unique gradient ids so multiple field instances never clash.
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '');
  const orbits = variant === 'full' ? ORBITS : ORBITS.filter((orbit) => orbit.tier === variant);

  return (
    <div
      className={`pointer-events-none absolute inset-0 flex items-center justify-center overflow-hidden ${className}`}
      aria-hidden="true"
    >
      <div className="relative aspect-square w-[min(165vmin,1750px)]">
        {/* Central bindu — the still point the system turns around. */}
        <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#B39250]/70 shadow-[0_0_24px_rgba(179,146,80,0.55)]" />

        {orbits.map((orbit, index) => {
          const gradientId = `${uid}-orbit-${index}`;
          const squash = orbit.squash;

          return (
            <div
              key={gradientId}
              className="absolute left-1/2 top-1/2"
              style={{
                width: `${orbit.size}%`,
                height: `${orbit.size}%`,
                transform: `translate(-50%, -50%) scaleY(${squash}) rotate(${orbit.offset}deg)`,
              }}
            >
              {/* Orbital path — warmer than the grid, fading into darkness on one arc. */}
              <svg
                className="absolute inset-0 h-full w-full"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={orbit.strokeColor} stopOpacity={orbit.strokeOpacity} />
                    <stop offset="45%" stopColor={orbit.strokeColor} stopOpacity={orbit.strokeOpacity * 0.55} />
                    <stop offset="100%" stopColor={orbit.strokeColor} stopOpacity="0" />
                  </linearGradient>
                </defs>
                <circle
                  cx="50"
                  cy="50"
                  r="49.4"
                  fill="none"
                  stroke={`url(#${gradientId})`}
                  strokeWidth="1"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>

              {/* Revolving bodies. Deep-tier bodies are thinned on small screens. */}
              <div
                className={`absolute inset-0 ${orbit.reverse ? 'kavach-orbit-reverse' : 'kavach-orbit'} ${
                  orbit.tier === 'deep' ? 'hidden sm:block' : ''
                }`}
                style={{ '--orbit-duration': `${orbit.duration}s` } as React.CSSProperties}
              >
                {orbit.bodies.map((body, bodyIndex) => {
                  const tone = TONES[body.tone];
                  const shadow = [
                    `inset -${(body.size * 0.1).toFixed(2)}px -${(body.size * 0.14).toFixed(2)}px ${(body.size * 0.3).toFixed(2)}px rgba(0,0,0,0.78)`,
                    `inset ${(body.size * 0.06).toFixed(2)}px ${(body.size * 0.06).toFixed(2)}px ${(body.size * 0.16).toFixed(2)}px rgba(255,238,214,0.2)`,
                    `0 0 ${(body.size * 1.1).toFixed(2)}px ${tone.glow}`,
                  ].join(', ');

                  return (
                    <span
                      key={bodyIndex}
                      className="kavach-planet absolute left-1/2 top-0 rounded-full"
                      style={{
                        width: body.size,
                        height: body.size,
                        background: tone.surface,
                        opacity: body.opacity,
                        boxShadow: shadow,
                        transform: `translate(-50%, -50%) scaleY(${(1 / squash).toFixed(3)})`,
                      }}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
