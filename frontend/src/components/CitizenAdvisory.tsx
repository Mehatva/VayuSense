import { useState, useEffect } from 'react'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import axios from 'axios'

interface Props { ward: string }

const LANGUAGES = [
  { code: 'English', name: 'ENG' },
  { code: 'Hindi', name: 'HIN' },
  { code: 'Kannada', name: 'KAN' },
  { code: 'Tamil', name: 'TAM' }
]

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function CitizenAdvisory({ ward }: Props) {
  const [lang, setLang] = useState('English')
  const [loading, setLoading] = useState(false)
  const [advisory, setAdvisory] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchAdvisory = async (selectedLang: string) => {
    try {
      setLoading(true)
      setError(null)
      const res = await axios.get(`${API}/api/citizen/advisory`, {
        params: {
          city: 'Delhi',
          ward: ward,
          language: selectedLang
        }
      })
      setAdvisory(res.data)
    } catch (err) {
      setError("Failed to generate advisory.")
    } finally {
      setLoading(false)
    }
  }

  // Fetch when ward changes or component mounts
  useEffect(() => {
    if (ward) {
      fetchAdvisory(lang)
    }
  }, [ward])

  const handleLang = (language: string) => {
    setLang(language)
    fetchAdvisory(language)
  }

  return (
    <>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={14} /> AI Advisory Generation
        </div>
        {advisory?.powered_by && (
          <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
             {advisory.powered_by}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {LANGUAGES.map(l => (
          <button
            key={l.code}
            onClick={() => handleLang(l.code)}
            style={{
              padding: '4px 12px', fontSize: 10, fontWeight: 600, fontFamily: 'var(--font-sans)',
              border: '1px solid var(--border-strong)',
              background: lang === l.code ? 'var(--slate-900)' : 'var(--bg-panel)',
              color: lang === l.code ? '#ffffff' : 'var(--text-primary)',
              cursor: 'pointer', borderRadius: 'var(--radius-sm)',
              transition: 'all 0.2s'
            }}
          >
            {l.name}
          </button>
        ))}
      </div>

      <div style={{
        background: 'var(--slate-50)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)', padding: '16px', minHeight: 120, 
        position: 'relative', fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)',
        display: 'flex', flexDirection: 'column',
      }}>
        {loading ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--text-secondary)', margin: 'auto' }}>
            <Loader2 size={14} className="animate-spin" />
            <span style={{ fontSize: 12, fontWeight: 500 }}>Generating via Gemini API...</span>
          </div>
        ) : error ? (
          <div style={{ color: 'var(--aqi-poor)', margin: 'auto', fontSize: 12 }}>{error}</div>
        ) : advisory ? (
          <div style={{ whiteSpace: 'pre-wrap' }}>{advisory.message}</div>
        ) : null}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        {['SMS', 'WHATSAPP'].map(channel => (
          <button key={channel} className="btn-primary" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border-strong)' }}>
            <Send size={12} /> {channel}
          </button>
        ))}
      </div>
    </>
  )
}
