// Deterministic checks for the Mars Rule (Rashi-based 4th and 8th aspects).
// Run with: npm run assert

import { computeMarsRule } from './marsRule'

let failures = 0

function expectEqual(actual: unknown, expected: unknown, label: string) {
  if (actual !== expected) {
    failures += 1
    console.error(`FAIL ${label}: expected ${expected}, got ${actual}`)
  }
}

// Test case: Mars in Libra (Rashi 7)
// 4th aspect: ((7 - 1 + 3) % 12) + 1 = 10 → Capricorn
// 8th aspect: ((7 - 1 + 7) % 12) + 1 = 2  → Taurus
const libra = computeMarsRule('Libra')
expectEqual(libra.marsRashiName, 'Libra', 'Libra marsRashiName')
expectEqual(libra.marsRashiNumber, 7, 'Libra marsRashiNumber')
expectEqual(libra.fourthAspectRashiName, 'Capricorn', 'Libra 4th aspect name')
expectEqual(libra.fourthAspectRashiNumber, 10, 'Libra 4th aspect number')
expectEqual(libra.eighthAspectRashiName, 'Taurus', 'Libra 8th aspect name')
expectEqual(libra.eighthAspectRashiNumber, 2, 'Libra 8th aspect number')

// Wrap-around: Mars in Aries (Rashi 1)
// 4th aspect: ((1 - 1 + 3) % 12) + 1 = 4 → Cancer
// 8th aspect: ((1 - 1 + 7) % 12) + 1 = 8 → Scorpio
const aries = computeMarsRule('Aries')
expectEqual(aries.marsRashiNumber, 1, 'Aries marsRashiNumber')
expectEqual(aries.fourthAspectRashiName, 'Cancer', 'Aries 4th aspect name')
expectEqual(aries.fourthAspectRashiNumber, 4, 'Aries 4th aspect number')
expectEqual(aries.eighthAspectRashiName, 'Scorpio', 'Aries 8th aspect name')
expectEqual(aries.eighthAspectRashiNumber, 8, 'Aries 8th aspect number')

// Unknown sign must be rejected
try {
  computeMarsRule('NotARashi')
  failures += 1
  console.error('FAIL unknown sign: expected an error to be thrown')
} catch {
  // expected
}

if (failures > 0) {
  throw new Error(`${failures} Mars Rule assertion(s) failed`)
}

console.log('Mars Rule assertions passed:')
console.log('  Mars in Libra (7): 4th aspect → Capricorn (10), 8th aspect → Taurus (2)')
console.log('  Mars in Aries (1): 4th aspect → Cancer (4),   8th aspect → Scorpio (8)')
