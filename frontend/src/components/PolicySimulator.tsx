import { useState } from 'react'
import { Play, FlaskConical } from 'lucide-react'

const SCENARIOS = [
  { id: 'trucks', label: 'Ban Heavy Diesel Vehicles', impact: 45 },
  { id: 'const', label: 'Halt Major Construction', impact: 30 },
  { id: 'indus', label: 'Shut Top 5 Polluting Factories', impact: 21 },
]

export default function PolicySimulator() {
  const [active, setActive] = useState<string[]>([])
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<number | null>(null)

  const toggle = (id: string) => {
    setActive(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
    setResult(null)
  }

  const runSim = () => {
    setRunning(true)
    setTimeout(() => {
      const totalReduction = active.reduce((acc, id) => {
        const s = SCENARIOS.find(x => x.id === id)
        return acc + (s ? s.impact : 0)
      }, 0)
      setResult(totalReduction)
      setRunning(false)
    }, 800)
  }

  return (
    <div className="panel" style={{ background: 'var(--bg-main)' }}>
      <div className="panel-header">
        <FlaskConical size={14} /> Policy Impact Simulator
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
        {SCENARIOS.map(s => {
          const isChecked = active.includes(s.id)
          return (
            <label key={s.id} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px', background: 'var(--bg-panel)',
              border: '1px solid var(--border-subtle)', cursor: 'pointer'
            }}>
              <input 
                type="checkbox" 
                checked={isChecked}
                onChange={() => toggle(s.id)}
                style={{ width: 14, height: 14, accentColor: 'var(--text-primary)' }}
              />
              <div style={{ flex: 1, fontSize: 11, fontWeight: 500 }}>{s.label}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--aqi-good)', fontWeight: 600 }}>
                -{s.impact} AQI
              </div>
            </label>
          )
        })}
      </div>

      <button 
        className="btn-primary" 
        onClick={runSim} 
        disabled={active.length === 0 || running}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
      >
        <Play size={14} />
        {running ? 'Simulating...' : 'Run Simulation'}
      </button>

      {result !== null && (
        <div style={{
          marginTop: 12, padding: '12px', background: 'var(--bg-panel)',
          border: '1px solid var(--border-focus)', textAlign: 'center'
        }}>
          <div className="data-label">Simulated AQI Reduction</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 24, fontWeight: 700, color: 'var(--aqi-good)' }}>
            -{result} pts
          </div>
        </div>
      )}
    </div>
  )
}
