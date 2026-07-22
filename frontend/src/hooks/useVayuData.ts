import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { LiveAQIData, WardAttribution, ForecastData, EnforcementTarget } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useVayuData(city: string, selectedWard: string) {
  const [liveData, setLiveData] = useState<LiveAQIData | null>(null)
  const [attribution, setAttribution] = useState<WardAttribution | null>(null)
  const [forecast, setForecast] = useState<ForecastData | null>(null)
  const [enforcement, setEnforcement] = useState<EnforcementTarget[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchGlobalData = useCallback(async () => {
    try {
      setLoading(true)
      const [aqiRes, enfRes] = await Promise.all([
        axios.get<LiveAQIData>(`${API}/api/aqi/live?city=${city}`),
        axios.get<EnforcementTarget[]>(`${API}/api/enforcement/actions?city=${city}&top_n=5`),
      ])
      setLiveData(aqiRes.data)
      setEnforcement(enfRes.data)
      setError(null)
    } catch (err) {
      if (err instanceof Error) setError(err)
      // Fallbacks can be added here if needed, but error states are preferred
    } finally {
      setLoading(false)
    }
  }, [city])

  const fetchWardData = useCallback(async () => {
    try {
      const [attrRes, fcstRes] = await Promise.all([
        axios.get<WardAttribution>(`${API}/api/attribution/${selectedWard}?city=${city}`),
        axios.get<ForecastData>(`${API}/api/forecast/${selectedWard}?city=${city}&hours=24`),
      ])
      setAttribution(attrRes.data)
      setForecast(fcstRes.data)
    } catch (err) {
      // Quiet fail for ward data to avoid breaking layout
    }
  }, [city, selectedWard])

  // Initial fetch and polling
  useEffect(() => {
    fetchGlobalData()
    const iv = setInterval(fetchGlobalData, 5 * 60 * 1000) // 5 min polling
    return () => clearInterval(iv)
  }, [fetchGlobalData])

  // Ward data fetch
  useEffect(() => {
    fetchWardData()
  }, [fetchWardData])

  return {
    liveData,
    attribution,
    forecast,
    enforcement,
    loading,
    error,
    API,
    currentAQI: liveData?.city_avg_aqi || 265 // Safe fallback for UI rendering
  }
}
