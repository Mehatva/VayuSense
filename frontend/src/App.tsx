import { useState } from 'react'
import { Wind, MapPin } from 'lucide-react'
import { useVayuData } from './hooks/useVayuData'
import CityMap from './components/CityMap'
import AttributionPanel from './components/AttributionPanel'
import ForecastChart from './components/ForecastChart'
import EnforcementPanel from './components/EnforcementPanel'
import EconomicCounter from './components/EconomicCounter'
import CitizenAdvisory from './components/CitizenAdvisory'

const CITIES = ['Delhi', 'Mumbai', 'Bengaluru']

function aqiClass(aqi: number) {
  if (aqi <= 50)  return 'aqi-good'
  if (aqi <= 100) return 'aqi-satisfactory'
  if (aqi <= 200) return 'aqi-moderate'
  if (aqi <= 300) return 'aqi-poor'
  if (aqi <= 400) return 'aqi-very-poor'
  return 'aqi-severe'
}

function aqiLabel(aqi: number) {
  if (aqi <= 50)  return 'Good'
  if (aqi <= 100) return 'Satisfactory'
  if (aqi <= 200) return 'Moderate'
  if (aqi <= 300) return 'Poor'
  if (aqi <= 400) return 'Very Poor'
  return 'Severe'
}

export default function App() {
  const [city, setCity] = useState('Delhi')
  const [selectedWard, setSelectedWard] = useState('Dwarka')
  const [forecastHour, setForecastHour] = useState(0)

  // Use the new custom hook
  const {
    attribution,
    forecast,
    enforcement,
    loading,
    API,
    currentAQI
  } = useVayuData(city, selectedWard)

  return (
    <div className="layout-wrapper">
      {/* ─── HEADER ─── */}
      <header className="layout-header">
        <div className="brand-logo">
          <Wind size={24} />
          VAYUSENSE
        </div>

        <div className="control-group">
          {CITIES.map(c => (
             <button 
              key={c} 
              className={`btn-segment ${city === c ? 'active' : ''}`}
              onClick={() => setCity(c)}
            >
              {c}
            </button>
          ))}
        </div>
      </header>

      {/* ─── FLUID GRID ─── */}
      <main className="dashboard-grid">
        
        {/* Map Panel */}
        <div className="panel grid-map" style={{ padding: 0 }}>
          <CityMap
            city={city}
            selectedWard={selectedWard}
            onWardSelect={setSelectedWard}
            forecastHour={forecastHour}
            currentAQI={currentAQI}
          />
          
          {/* Subtle overlay slider */}
          <div style={{
            position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)',
            zIndex: 1000, background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)',
            border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)',
            padding: '12px 24px', display: 'flex', alignItems: 'center', gap: 16,
            boxShadow: 'var(--shadow-md)'
          }}>
            <span style={{ fontSize: 12, fontWeight: 500 }}>Now</span>
            <input
              type="range" min={0} max={72} step={1}
              value={forecastHour}
              onChange={e => setForecastHour(Number(e.target.value))}
              style={{ width: 180, accentColor: 'var(--slate-900)' }}
            />
            <span style={{ fontSize: 12, fontWeight: 500 }}>+72h</span>
          </div>
        </div>

        {/* AQI Summary Panel */}
        <div className="panel grid-aqi" style={{ justifyContent: 'center', alignItems: 'center' }}>
           <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', marginBottom: 16, fontSize: 13, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
             <MapPin size={14} /> {city} Index
           </div>
           <div className={`metric-value ${aqiClass(currentAQI)}`} style={{ fontSize: 72, marginBottom: 8 }}>
             {currentAQI}
           </div>
           <div className={aqiClass(currentAQI)} style={{ fontSize: 16, fontWeight: 600 }}>
             {aqiLabel(currentAQI)}
           </div>
        </div>

        {/* Economic Damage Panel */}
        <div className="panel grid-eco" style={{ background: 'var(--slate-900)', color: 'white' }}>
           <EconomicCounter city={city} api={API} />
        </div>

        {/* Forecast Panel */}
        <div className="panel grid-forecast">
           <ForecastChart data={forecast} ward={selectedWard} />
        </div>
        
        {/* Attribution Panel */}
        <div className="panel grid-attr">
           <AttributionPanel ward={selectedWard} data={attribution} onWardChange={setSelectedWard} />
        </div>

        {/* Enforcement Panel */}
        <div className="panel grid-enf">
           <EnforcementPanel data={enforcement} loading={loading} />
        </div>

        {/* Advisory Gen Panel */}
        <div className="panel grid-advisory">
           <CitizenAdvisory ward={selectedWard} />
        </div>

      </main>
    </div>
  )
}
