import { useState, useEffect } from 'react'
import { TrendingDown, Calculator } from 'lucide-react'
import axios from 'axios'

interface Props { city: string; api: string }

export default function EconomicCounter({ city, api }: Props) {
  const [total, setTotal] = useState(0)
  const [perMin, setPerMin] = useState(450000)

  useEffect(() => {
    axios.get(`${api}/api/metrics/damage?city=${city}`).then(res => {
      setTotal(res.data.daily_total_inr)
      setPerMin(res.data.per_minute_inr)
    }).catch(() => {
      setTotal(85400000)
      setPerMin(450000)
    })
  }, [city, api])

  useEffect(() => {
    const iv = setInterval(() => {
      setTotal(prev => prev + (perMin / 60))
    }, 1000)
    return () => clearInterval(iv)
  }, [perMin])

  const crore = (total / 1e7).toFixed(2)
  const perMinStr = `₹${perMin.toLocaleString('en-IN')} / min`

  return (
    <>
      <div className="panel-title" style={{ color: 'rgba(255,255,255,0.7)', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: 16 }}>
        <TrendingDown size={16} /> Est. Economic Damage
      </div>
      
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 16 }}>
        <div style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-0.04em', lineHeight: 1 }}>
          ₹{crore}
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
          Crores Today
        </div>
      </div>
      
      <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#f87171', fontWeight: 600 }}>
        <Calculator size={14} /> BURN RATE: {perMinStr}
      </div>
    </>
  )
}
