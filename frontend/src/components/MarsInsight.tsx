import type { MarsRuleResult } from '../lib/marsRule'
import { RASHI_SANSKRIT_NAMES } from '../data/rashis'
import { RASHI_THEMES } from '../data/rashiThemes'

export default function MarsInsight({ result }: { result: MarsRuleResult }) {
  const sanskrit = RASHI_SANSKRIT_NAMES[result.marsRashiNumber - 1]
  const fourthTheme = RASHI_THEMES[result.fourthAspectRashiName]
  const eighthTheme = RASHI_THEMES[result.eighthAspectRashiName]

  return (
    <div className="mars-insight">
      <div className="mars-block">
        <div className="mars-label">MARS RULE</div>
        <div className="mars-title">Mars in {result.marsRashiName}</div>
        <div className="mars-sub">
          Rashi {result.marsRashiNumber} — {sanskrit}
        </div>
      </div>

      <div className="mars-block aspect">
        <div className="mars-label">MARS'S 4TH ASPECT</div>
        <div className="mars-value">
          Mars's 4th aspect falls on {result.fourthAspectRashiName} (Rashi{' '}
          {result.fourthAspectRashiNumber}).
        </div>
        <div className="mars-text">
          {result.fourthAspectRashiName} represents {fourthTheme}. Therefore, this is
          an area where the person should remain careful, disciplined and cautious.
        </div>
      </div>

      <div className="mars-block aspect">
        <div className="mars-label">MARS'S 8TH ASPECT</div>
        <div className="mars-value">
          Mars's 8th aspect falls on {result.eighthAspectRashiName} (Rashi{' '}
          {result.eighthAspectRashiNumber}).
        </div>
        <div className="mars-text">
          {result.eighthAspectRashiName} represents {eighthTheme}. Mars's 8th aspect
          indicates the need for awareness, preparation and thoughtful handling of
          these matters, especially when circumstances change unexpectedly.
        </div>
      </div>

      <div className="mars-footer">
        These areas may benefit from extra patience, preparation and thoughtful
        decision-making.
      </div>
    </div>
  )
}
