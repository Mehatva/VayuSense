import { PieChart } from 'lucide-react'

const WARDS = ['Dwarka','Rohini','Connaught Place','Anand Vihar','Okhla','Punjabi Bagh','R.K. Puram','Shahdara']

const DEMO_ATTRIBUTION: Record<string, any[]> = {
  Dwarka: [
    { label: 'Construction Dust', contribution_pct: 61 },
    { label: 'Vehicle Exhaust',   contribution_pct: 28 },
    { label: 'Biomass Burning',   contribution_pct: 8  },
    { label: 'Road / Soil Dust',  contribution_pct: 3  },
  ],
  'Anand Vihar': [
    { label: 'Vehicle Exhaust',   contribution_pct: 52 },
    { label: 'Construction Dust', contribution_pct: 22 },
    { label: 'Road / Soil Dust',  contribution_pct: 16 },
    { label: 'Industrial',        contribution_pct: 10 },
  ],
  Okhla: [
    { label: 'Industrial',        contribution_pct: 48 },
    { label: 'Vehicle Exhaust',   contribution_pct: 32 },
    { label: 'Road / Soil Dust',  contribution_pct: 12 },
    { label: 'Construction Dust', contribution_pct: 8  },
  ],
}
const DEFAULT_ATTR = DEMO_ATTRIBUTION['Dwarka']

interface Props { ward: string; data: any; onWardChange: (w: string) => void }

export default function AttributionPanel({ ward, data, onWardChange }: Props) {
  const sources = data?.sources || DEMO_ATTRIBUTION[ward] || DEFAULT_ATTR
  const topSource = data?.top_source || 'NH-48 Airport Expansion Site'
  const confidence = data?.confidence ? Math.round(data.confidence * 100) : 83

  return (
    <>
      <div className="panel-title">
        <PieChart size={14} /> Source Attribution
      </div>

      <select
        value={ward}
        onChange={e => onWardChange(e.target.value)}
        className="select-minimal"
        style={{ marginBottom: 12 }}
      >
        {WARDS.map(w => <option key={w}>{w}</option>)}
      </select>

      <table className="data-table">
        <thead>
          <tr>
            <th>Source Category</th>
            <th style={{ width: '40%' }}>% Impact</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s: any, i: number) => (
            <tr key={i}>
              <td style={{ fontWeight: 500 }}>{s.label}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div className="flat-bar-bg">
                    <div className="flat-bar-fill" style={{ width: `${s.contribution_pct}%` }} />
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, width: 30, textAlign: 'right' }}>
                    {Math.round(s.contribution_pct)}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{
        marginTop: 12, padding: 8,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-main)',
        fontSize: 11
      }}>
        <div style={{ fontWeight: 700, textTransform: 'uppercase', marginBottom: 4 }}>Primary Vector</div>
        <div style={{ color: 'var(--text-secondary)' }}>{topSource}</div>
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between',
        marginTop: 12, fontSize: 10, color: 'var(--text-tertiary)',
        fontFamily: 'var(--font-mono)'
      }}>
        <span>SRC: Sentinel-5P</span>
        <span>CONF: {confidence}%</span>
      </div>
    </>
  )
}
