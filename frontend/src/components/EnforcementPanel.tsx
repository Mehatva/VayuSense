import { useState } from 'react'
import { Target, FileText } from 'lucide-react'

const DEMO_ACTIONS = [
  { id: 'ACT-1092', ward: 'Dwarka', target: 'NH-48 Construction Site', priority: 'HIGH',   aqi_impact: 42, days_active: 12 },
  { id: 'ACT-1093', ward: 'Anand Vihar', target: 'ISBT Idling Zone',   priority: 'HIGH',   aqi_impact: 38, days_active: 4 },
  { id: 'ACT-1094', ward: 'Okhla', target: 'Phase 2 Textiles',         priority: 'MEDIUM', aqi_impact: 21, days_active: 8 },
  { id: 'ACT-1095', ward: 'Rohini', target: 'Sector 3 Waste Burn',     priority: 'LOW',    aqi_impact: 12, days_active: 2 },
]

function getPriorityColor(priority: string) {
  if (priority === 'HIGH') return 'var(--aqi-very-poor)'
  if (priority === 'MEDIUM') return 'var(--aqi-poor)'
  return 'var(--aqi-moderate)'
}

export default function EnforcementPanel({ data, loading }: { data: any; loading: boolean }) {
  const actions = data?.actions || DEMO_ACTIONS
  const [expanded, setExpanded] = useState<string | null>(null)

  return (
    <>
      <div className="panel-title">
        <Target size={14} /> Active Enforcement Targets
      </div>

      {loading ? (
        <div style={{ height: 200, background: 'var(--border-subtle)' }} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {actions.map((act: any) => (
            <div
              key={act.id}
              onClick={() => setExpanded(expanded === act.id ? null : act.id)}
              style={{
                border: '1px solid var(--border-subtle)',
                borderLeft: `3px solid ${getPriorityColor(act.priority)}`,
                padding: '10px', background: expanded === act.id ? 'var(--bg-main)' : 'var(--bg-panel)',
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 2 }}>
                    {act.id} | {act.ward}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 12 }}>{act.target}</div>
                </div>
                <div style={{
                  fontSize: 9, fontWeight: 700, padding: '2px 6px',
                  background: 'var(--bg-panel)', border: `1px solid ${getPriorityColor(act.priority)}`,
                  color: getPriorityColor(act.priority), letterSpacing: '0.05em'
                }}>
                  {act.priority}
                </div>
              </div>

              {expanded === act.id && (
                <div style={{
                  marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                    <div>
                      <div className="data-label">Est. AQI Impact</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: 'var(--aqi-good)' }}>
                        -{act.aqi_impact} pts
                      </div>
                    </div>
                    <div>
                      <div className="data-label">Violation Duration</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>
                        {act.days_active} Days
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ background: 'var(--bg-panel)', border: '1px dashed var(--border-hard)', padding: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', marginBottom: 4, color: 'var(--text-secondary)' }}>
                      <FileText size={12} /> AI Evidence Brief
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                      Sentinel-5P anomaly detected. PM10 levels deviate +40% from baseline at {act.target}. Recommend immediate dispatch of inspection team.
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}
