import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet'

const MAP_TILES = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'

const CITIES: Record<string, [number, number]> = {
  Delhi: [28.6139, 77.2090],
  Mumbai: [19.0760, 72.8777],
  Bengaluru: [12.9716, 77.5946]
}

const DEMO_STATIONS = [
  { id: 'Dwarka', lat: 28.5921, lng: 77.0460, baseAqi: 280 },
  { id: 'Rohini', lat: 28.7041, lng: 77.1025, baseAqi: 310 },
  { id: 'Connaught Place', lat: 28.6304, lng: 77.2177, baseAqi: 190 },
  { id: 'Anand Vihar', lat: 28.6469, lng: 77.3160, baseAqi: 380 },
  { id: 'Okhla', lat: 28.5272, lng: 77.2773, baseAqi: 240 },
  { id: 'Punjabi Bagh', lat: 28.6619, lng: 77.1241, baseAqi: 290 },
  { id: 'R.K. Puram', lat: 28.5659, lng: 77.1711, baseAqi: 220 },
  { id: 'Shahdara', lat: 28.6987, lng: 77.2917, baseAqi: 330 },
]

function aqiColor(aqi: number) {
  if (aqi <= 50) return 'var(--aqi-good)'
  if (aqi <= 100) return 'var(--aqi-satisfactory)'
  if (aqi <= 200) return 'var(--aqi-moderate)'
  if (aqi <= 300) return 'var(--aqi-poor)'
  if (aqi <= 400) return 'var(--aqi-very-poor)'
  return 'var(--aqi-severe)'
}

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => { map.setView(center, 11) }, [center, map])
  return null
}

interface Props { city: string; selectedWard: string; onWardSelect: (w: string) => void; forecastHour: number; currentAQI: number }

export default function CityMap({ city, selectedWard, onWardSelect, forecastHour }: Props) {
  const center = CITIES[city] || CITIES.Delhi

  return (
    <MapContainer 
      center={center} 
      zoom={11} 
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer url={MAP_TILES} />
      <MapUpdater center={center} />

      {city === 'Delhi' && DEMO_STATIONS.map(s => {
        const simulatedAqi = s.baseAqi + Math.sin(forecastHour/3) * 50 + (forecastHour * 2)
        const color = aqiColor(simulatedAqi)
        const isSelected = selectedWard === s.id
        
        return (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lng]}
            radius={isSelected ? 10 : 7}
            pathOptions={{ 
              color: 'var(--text-primary)', 
              fillColor: color, 
              fillOpacity: 1, 
              weight: isSelected ? 3 : 1
            }}
            eventHandlers={{ click: () => onWardSelect(s.id) }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent={isSelected}>
              <div style={{ padding: '2px', textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 10, textTransform: 'uppercase' }}>{s.id}</div>
                <div style={{ fontFamily: 'var(--font-mono)', color, fontWeight: 700, fontSize: 14 }}>
                  {Math.round(simulatedAqi)}
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
