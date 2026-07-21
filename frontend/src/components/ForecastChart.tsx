import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { LineChart, Wind, Activity } from 'lucide-react'

function aqiColor(aqi: number) {
  if (aqi <= 50)  return 'var(--aqi-good)'
  if (aqi <= 100) return 'var(--aqi-satisfactory)'
  if (aqi <= 200) return 'var(--aqi-moderate)'
  if (aqi <= 300) return 'var(--aqi-poor)'
  if (aqi <= 400) return 'var(--aqi-very-poor)'
  return 'var(--aqi-severe)'
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const aqi = data.predicted_aqi
    return (
      <div style={{
        background: 'var(--bg-panel)',
        border: `1px solid var(--border-strong)`,
        padding: '12px',
        fontSize: 12,
        fontFamily: 'var(--font-mono)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-md)',
        minWidth: '160px'
      }}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>
          {data.hour_label}
        </div>
        <div style={{ fontSize: 24, fontWeight: 700, color: aqiColor(aqi), marginBottom: 8 }}>
          AQI {aqi}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Activity size={12} /> PM2.5</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{data.pm25_estimate} µg/m³</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Wind size={12} /> Wind</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{data.wind_speed} km/h</span>
          </div>
        </div>
      </div>
    )
  }
  return null
}

export default function ForecastChart({ data, ward }: { data: any; ward: string }) {
  // Use real backend data if available, fallback to empty array (or gracefully handle missing)
  const points = data?.hourly || []

  return (
    <>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LineChart size={14} /> 72H Predictive Forecast
        </div>
        {data?.weather_source && (
          <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
            Powered by {data.weather_source}
          </div>
        )}
      </div>
      
      <div style={{ flex: 1, minHeight: 180, marginTop: 8 }}>
        {points.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 4, right: 0, bottom: 0, left: -30 }}>
              <XAxis 
                dataKey="hour_label" 
                stroke="var(--border-strong)" 
                fontSize={10} 
                tickMargin={8} 
                fontFamily="var(--font-mono)"
                tickFormatter={(val) => {
                  // Shorten to just time (e.g. 06AM)
                  const parts = val.split(' ')
                  return parts.length > 2 ? parts[2] : val
                }} 
              />
              <YAxis stroke="var(--border-strong)" fontSize={10} fontFamily="var(--font-mono)" />
              <Tooltip content={<CustomTooltip />} />
              
              <ReferenceLine y={200} stroke="var(--aqi-poor)" strokeDasharray="3 3" opacity={0.5} />
              <ReferenceLine y={300} stroke="var(--aqi-very-poor)" strokeDasharray="3 3" opacity={0.5} />
              
              <Area 
                type="monotone" 
                dataKey="predicted_aqi" 
                stroke="var(--slate-900)" 
                strokeWidth={2}
                fill="var(--border-subtle)" 
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-tertiary)', fontSize: 13 }}>
            Loading predictive model...
          </div>
        )}
      </div>
      
      <div style={{ display: 'flex', gap: 12, marginTop: 12, fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
        <div><span style={{color:'var(--aqi-poor)'}}>---</span> WARN (200)</div>
        <div><span style={{color:'var(--aqi-very-poor)'}}>---</span> CRIT (300)</div>
      </div>
    </>
  )
}
