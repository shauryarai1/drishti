import { RASHI_NAMES } from '../data/rashis'

export type MarsRuleResult = {
  marsRashiName: string
  marsRashiNumber: number
  fourthAspectRashiName: string
  fourthAspectRashiNumber: number
  eighthAspectRashiName: string
  eighthAspectRashiNumber: number
}

// Mars Rule: everything is calculated from Mars's RASHI only.
// Mars's chart position (house) is never used as an input.
//
//   4th aspect: ((marsRashiNumber - 1 + 3) % 12) + 1
//   8th aspect: ((marsRashiNumber - 1 + 7) % 12) + 1
export function computeMarsRule(marsSign: string): MarsRuleResult {
  const index = RASHI_NAMES.indexOf(marsSign)
  if (index < 0) {
    throw new Error(`Unknown Mars sign: ${marsSign}`)
  }

  const marsRashiNumber = index + 1
  const fourthAspectRashiNumber = ((marsRashiNumber - 1 + 3) % 12) + 1
  const eighthAspectRashiNumber = ((marsRashiNumber - 1 + 7) % 12) + 1

  return {
    marsRashiName: RASHI_NAMES[index],
    marsRashiNumber,
    fourthAspectRashiName: RASHI_NAMES[fourthAspectRashiNumber - 1],
    fourthAspectRashiNumber,
    eighthAspectRashiName: RASHI_NAMES[eighthAspectRashiNumber - 1],
    eighthAspectRashiNumber,
  }
}
