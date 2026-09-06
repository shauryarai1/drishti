export interface InterpretationArea {
  area: string
  severity: string
  severity_level: 'low' | 'moderate' | 'high'
  hook?: string
  description: string
  potential_impact: string
  mindful_of: string[]
  takeaway: string
}

export interface ChartPlanet {
  name: string
  sign: string
  house: number
  degree: number
}

export interface ChartHouse {
  number: number
  sign: string
}

export interface ChartData {
  ascendant_sign: string | null
  planets: ChartPlanet[]
  extra_planets?: ChartPlanet[]
  houses: ChartHouse[]
}

export interface InterpretationResponse {
  status: 'success' | 'error'
  message?: string
  primary: InterpretationArea
  secondary: InterpretationArea
  sudden?: InterpretationArea
  chart?: ChartData
}

export interface BirthPayload {
  date: string
  time: string
  place: string
}
