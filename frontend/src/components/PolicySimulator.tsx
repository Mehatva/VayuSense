import { useState, useEffect } from 'react'
import { Play, FlaskConical, Loader2, Info } from 'lucide-react'
import axios from 'axios'
import type { Scenario, SimulationResult } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Props {
  city: string;
}

export default function PolicySimulator({ city }: Props) {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [active, setActive] = useState<string[]>([])
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<SimulationResult[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get(`${API}/api/simulator/scenarios`)
      .then(res => setScenarios(res.data.scenarios))
      .catch(err => setError('Failed to load scenarios'))
  }, [])

  const toggle = (id: string) => {
    setActive(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
    setResults([])
  }

  const runSim = async () => {
    if (active.length === 0) return
    setRunning(true)
    setError(null)
    
    try {
      const res = await axios.post(`${API}/api/simulator/run`, {
        city: city,
        scenarios: active,
        hour_offset: 6
      })
      setResults(res.data.results)
    } catch (err) {
      setError('Simulation failed')
    } finally {
      setRunning(false)
    }
  }

  // Calculate city-wide average improvement
  const avgImprovement = results.length > 0 
    ? Math.round(results.reduce((acc, r) => acc + r.aqi_improvement, 0) / results.length)
    : null

  return (
    <>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FlaskConical size={14} /> Causal Policy Simulator
        </div>
        <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
           <Info size={12} /> T+6H Projection
        </div>
      </div>

      {error && <div style={{ color: 'var(--aqi-poor)', fontSize: 12, marginBottom: 8 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Left Column: Scenarios */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {scenarios.map(s => {
            const isChecked = active.includes(s.id)
            return (
              <label key={s.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '12px', background: isChecked ? 'var(--slate-50)' : 'var(--bg-panel)',
                border: `1px solid ${isChecked ? 'var(--slate-400)' : 'var(--border-subtle)'}`, 
                cursor: 'pointer', borderRadius: 'var(--radius-sm)', transition: 'all 0.2s'
              }}>
                <input 
                  type="checkbox" 
                  checked={isChecked}
                  onChange={() => toggle(s.id)}
                  style={{ width: 14, height: 14, accentColor: 'var(--text-primary)', marginTop: 2 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{s.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{s.description}</div>
                </div>
              </label>
            )
          })}
          
          <button 
            className="btn-primary" 
            onClick={runSim} 
            disabled={active.length === 0 || running}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 8 }}
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? 'Simulating Physics & Wind...' : 'Execute Counterfactual Simulation'}
          </button>
        </div>

        {/* Right Column: Results */}
        <div style={{ background: 'var(--slate-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: '16px', display: 'flex', flexDirection: 'column' }}>
           {results.length > 0 ? (
             <>
               <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 16 }}>
                 Simulation Results (City-Wide)
               </div>
               <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 24 }}>
                 <div style={{ fontSize: 48, fontWeight: 700, color: 'var(--aqi-good)', lineHeight: 1, letterSpacing: '-0.04em' }}>
                   -{avgImprovement}
                 </div>
                 <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                   Avg. AQI Reduction
                 </div>
               </div>

               <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 8, borderBottom: '1px solid var(--border-strong)', paddingBottom: 4 }}>
                 Ward-Level Impact
               </div>
               <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto', flex: 1 }}>
                 {results.sort((a,b) => b.aqi_improvement - a.aqi_improvement).map(r => (
                   <div key={r.ward} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                     <span style={{ fontSize: 12, fontWeight: 500 }}>{r.ward}</span>
                     <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                       <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textDecoration: 'line-through' }}>{r.baseline_aqi}</span>
                       <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{r.intervention_aqi}</span>
                       <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--aqi-good)', width: '40px', textAlign: 'right' }}>
                         -{Math.round(r.improvement_pct)}%
                       </span>
                     </div>
                   </div>
                 ))}
               </div>
             </>
           ) : (
             <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', padding: '0 24px' }}>
               Select policy interventions on the left to simulate their compounded impact on urban air quality.
             </div>
           )}
        </div>
      </div>
    </>
  )
}
