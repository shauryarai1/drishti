import type { ChartResponse } from '../types/chart'

const RASHI_NAMES = [
  'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

const ABBREVIATIONS: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl'
}

// 3.png is 1254x1254 and is used unchanged as the fixed visual background.
// Overlay coordinates are percentages of the image/container so they remain
// aligned for any responsive size.
const HOUSE_POSITIONS: Record<number, { x: number; y: number }> = {
  1:  { x: 0.50, y: 0.17 }, // top-center
  2:  { x: 0.23, y: 0.27 }, // upper-left
  3:  { x: 0.15, y: 0.40 }, // left-upper
  4:  { x: 0.15, y: 0.54 }, // left-middle
  5:  { x: 0.23, y: 0.68 }, // left-lower
  6:  { x: 0.35, y: 0.80 }, // bottom-left
  7:  { x: 0.50, y: 0.84 }, // bottom-center
  8:  { x: 0.65, y: 0.80 }, // bottom-right
  9:  { x: 0.77, y: 0.68 }, // right-lower
  10: { x: 0.85, y: 0.54 }, // right-middle
  11: { x: 0.85, y: 0.40 }, // right-upper
  12: { x: 0.77, y: 0.27 }, // upper-right
}

export default function KundliChart({ chart }: { chart: ChartResponse }) {
  const houseMap = new Map((chart.houses || []).map(h => [h.number, h]))
  const mainPlanetsByHouse = new Map<number, typeof chart.planets>()
  const extraPlanetsByHouse = new Map<number, typeof chart.extra_planets>()

  for (const p of chart.planets || []) {
    const list = mainPlanetsByHouse.get(p.house) || []
    list.push(p)
    mainPlanetsByHouse.set(p.house, list)
  }

  for (const p of chart.extra_planets || []) {
    const list = extraPlanetsByHouse.get(p.house) || []
    list.push(p)
    extraPlanetsByHouse.set(p.house, list)
  }

  return (
    <div className="kundli-wrap">
      <div className="kundli-container">
        {/* The 3.png template is used as background */}
        <img 
          src="/3.png" 
          alt="North Indian Kundli Template" 
          className="kundli-template"
        />
        
        {/* Overlay for house content positioned over the template */}
        <div className="kundli-overlay">
          {Array.from({ length: 12 }, (_, i) => {
            const houseNumber = i + 1
            const house = houseMap.get(houseNumber)
            const signName = house?.sign || RASHI_NAMES[houseNumber - 1]
            const signIndex = RASHI_NAMES.indexOf(signName)
            const mainPlanets = mainPlanetsByHouse.get(houseNumber) || []
            const extraPlanets = extraPlanetsByHouse.get(houseNumber) || []

            const pos = HOUSE_POSITIONS[houseNumber]

            return (
              <div
                key={houseNumber}
                className="house-overlay"
                style={{
                  position: 'absolute',
                  left: `${pos.x * 100}%`,
                  top: `${pos.y * 100}%`,
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  zIndex: 10
                }}
              >
                <div style={{ fontSize: '10px', color: '#8A827A', marginBottom: '2px' }}>
                  {houseNumber}
                </div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#17130F', marginBottom: '2px' }}>
                  {signIndex >= 0 ? signIndex + 1 : houseNumber}
                </div>
                <div style={{ fontSize: '11px', color: '#17130F', marginBottom: '4px' }}>
                  {signName}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                  {mainPlanets.length > 0 && (
                    <div style={{ fontSize: '9px', color: '#17130F', lineHeight: 1.1 }}>
                      {mainPlanets.map(p => ABBREVIATIONS[p.name] || p.name).join(' ')}
                    </div>
                  )}
                  {extraPlanets.length > 0 && (
                    <div style={{ fontSize: '8px', color: '#C9A024', lineHeight: 1.1 }}>
                      {extraPlanets.map(p => ABBREVIATIONS[p.name] || p.name).join(' ')}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
