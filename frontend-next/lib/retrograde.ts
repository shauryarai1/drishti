/**
 * Retrograde display helper for the Kundli result.
 *
 * Presentation only. The retrograde state is NOT derived here: it is read from
 * the authoritative `motion` value the KAVACH backend already produces with its
 * approved motion logic.
 *
 * The motion model classifies each body as one of:
 *   - "Retrograde" - an ordinary planet moving retrograde at birth
 *   - "Direct"     - an ordinary planet moving direct
 *   - "Node"       - Rahu / Ketu, which KAVACH deliberately treats separately
 *
 * Nodes are therefore never listed as retrograde, and nothing is recomputed here.
 */

import type { KundliPlanet } from './kundli';

export const MOTION_RETROGRADE = 'Retrograde';
export const MOTION_DIRECT = 'Direct';
export const MOTION_NODE = 'Node';

/** Only the planets the existing KAVACH motion model marks Retrograde. */
export function retrogradePlanets(
  planets: KundliPlanet[] | null | undefined,
): KundliPlanet[] {
  return (planets ?? []).filter((planet) => planet?.motion === MOTION_RETROGRADE);
}
