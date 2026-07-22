export interface LiveAQIData {
  station_count: number;
  city_avg_aqi: number;
  worst_ward: {
    station: string;
    aqi: number;
  };
}

export interface WardAttribution {
  ward: string;
  top_source: string;
  confidence: number;
  data: { name: string; value: number }[];
}

export interface ForecastData {
  ward: string;
  forecast: { time: string; aqi: number }[];
}

export interface EnforcementTarget {
  id: string
  ward: string
  lat: number
  lon: number
  violation_type: string
  confidence_score: number
  severity: 'high' | 'medium' | 'low'
  est_emissions_kg_hr: number
  status: 'active' | 'investigating' | 'resolved'
}

export interface IoTEvent {
  id: string
  ward: string
  timestamp: string
  metric: string
  delta: string
  severity: 'high' | 'medium'
  cause: string
}

export interface Scenario {
  id: string
  label: string
  description: string
}

export interface SimulationResult {
  ward: string
  baseline_aqi: number
  intervention_aqi: number
  aqi_improvement: number
  improvement_pct: number
  category_before: string
}
