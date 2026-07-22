import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import type { LiveAQIData, WardAttribution, ForecastData, EnforcementTarget, IoTEvent } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_URL = API.replace('http', 'ws')

export function useVayuData(city: string, selectedWard: string) {
  const [liveData, setLiveData] = useState<LiveAQIData | null>(null)
  const [attribution, setAttribution] = useState<WardAttribution | null>(null)
  const [forecast, setForecast] = useState<ForecastData | null>(null)
  const [enforcement, setEnforcement] = useState<EnforcementTarget[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  
  // IoT Events Stream
  const [iotEvents, setIotEvents] = useState<IoTEvent[]>([])
  const ws = useRef<WebSocket | null>(null)

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
      // Quiet fail
    }
  }, [city, selectedWard])

  // HTTP Polling
  useEffect(() => {
    fetchGlobalData()
    const iv = setInterval(fetchGlobalData, 5 * 60 * 1000)
    return () => clearInterval(iv)
  }, [fetchGlobalData])

  useEffect(() => {
    fetchWardData()
  }, [fetchWardData])

  // WebSocket Live Stream Connection
  useEffect(() => {
    ws.current = new WebSocket(`${WS_URL}/ws/live-updates?city=${city}`)
    
    ws.current.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'iot_spike') {
          // Prepend new event and keep last 5
          setIotEvents(prev => [payload.data, ...prev].slice(0, 5))
        }
      } catch (err) {
        console.error("WebSocket message parse error", err)
      }
    }

    return () => {
      ws.current?.close()
    }
  }, [city])

  return {
    liveData,
    attribution,
    forecast,
    enforcement,
    iotEvents,
    loading,
    error,
    API,
    currentAQI: liveData?.city_avg_aqi || 265
  }
}
