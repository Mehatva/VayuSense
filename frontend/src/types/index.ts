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
  id: string;
  name: string;
  type: string;
  violation_score: number;
  lat: number;
  lon: number;
}
