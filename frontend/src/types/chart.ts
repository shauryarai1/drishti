export interface ChartResponse {
  status: string
  reason?: string
  settings?: Record<string, string>
  birth?: {
    date: string
    time: string
    place: string
    latitude: number
    longitude: number
    timezone: string
    utc_datetime: string
  }
  ascendant?: {
    longitude: number
    sign: string
    house: number
    degree: number
  }
  planets?: Array<{
    name: string
    longitude: number
    sign: string
    house: number
    degree: number
    nakshatra?: string
    pada?: number
    source: string
    status: string
  }>
  houses?: Array<{
    number: number
    sign: string
    cusp_longitude: number
  }>
  validation?: {
    passed: boolean
    checks: Array<{
      name: string
      passed: boolean
      detail?: string
    }>
  }
  debug?: string
  extra_planets?: Array<{
    name: string
    longitude: number
    sign: string
    house: number
    degree: number
    source: string
    status: string
  }>
}

export interface ChartPayload {
  date: string
  time: string
  place: string
  ayanamsa?: string
}