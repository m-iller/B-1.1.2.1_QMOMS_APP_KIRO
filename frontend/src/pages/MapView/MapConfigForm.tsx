import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getMapConfig, putMapConfig } from '../../api/mapConfig'
import type { AntennaDefinition, MapConfigRequest } from '../../types/api.types'

const DEFAULT_ANTENNAS: AntennaDefinition[] = [
  { name: 'Antenna A', lat: 0, lng: 0 },
  { name: 'Antenna B', lat: 0, lng: 0 },
  { name: 'Antenna C', lat: 0, lng: 0 },
]

export function MapConfigForm() {
  const { user } = useAuth()
  const canEdit = user?.role === 'dispatcher' || user?.role === 'admin' || user?.role === 'dev'

  const [open, setOpen] = useState(false)
  const [centerLat, setCenterLat] = useState('')
  const [centerLng, setCenterLng] = useState('')
  const [zoom, setZoom] = useState('15')
  const [antennas, setAntennas] = useState<AntennaDefinition[]>(DEFAULT_ANTENNAS)
  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!open) return
    getMapConfig()
      .then(cfg => {
        setCenterLat(String(cfg.center_lat))
        setCenterLng(String(cfg.center_lng))
        setZoom(String(cfg.default_zoom))
        setAntennas(cfg.antennas.length > 0 ? cfg.antennas : DEFAULT_ANTENNAS)
      })
      .catch(err => {
        if (err?.response?.status === 404) {
          setCenterLat('')
          setCenterLng('')
          setZoom('15')
          setAntennas(DEFAULT_ANTENNAS)
        }
      })
  }, [open])

  const updateAntenna = (idx: number, field: keyof AntennaDefinition, value: string) => {
    setAntennas(prev => prev.map((a, i) =>
      i === idx ? { ...a, [field]: field === 'name' ? value : parseFloat(value) || 0 } : a
    ))
  }

  const addAntenna = () => setAntennas(prev => [...prev, { name: `Antenna ${prev.length + 1}`, lat: 0, lng: 0 }])
  const removeAntenna = (idx: number) => {
    if (antennas.length <= 1) return
    setAntennas(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('saving')
    setErrorMsg('')
    const payload: MapConfigRequest = {
      center_lat: parseFloat(centerLat),
      center_lng: parseFloat(centerLng),
      default_zoom: parseInt(zoom, 10),
      antennas,
    }
    try {
      await putMapConfig(payload)
      setStatus('success')
      setTimeout(() => setStatus('idle'), 2000)
    } catch (err: any) {
      setStatus('error')
      setErrorMsg(err?.response?.data?.message || 'Failed to save configuration')
    }
  }

  if (!canEdit) return null

  return (
    <div style={{ marginTop: 16 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ padding: '6px 14px', background: '#374151', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}
      >
        ⚙ {open ? 'Close' : 'Configure Map'}
      </button>

      {open && (
        <form onSubmit={handleSubmit} style={{ marginTop: 12, padding: 16, border: '1px solid #e5e7eb', borderRadius: 8, background: '#f9fafb', maxWidth: 600 }}>
          <h4 style={{ margin: '0 0 12px' }}>Map Configuration</h4>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
            <label style={{ fontSize: 13 }}>
              Center Lat
              <input type="number" step="any" value={centerLat} onChange={e => setCenterLat(e.target.value)} required
                style={{ display: 'block', width: '100%', padding: '4px 6px', marginTop: 2, border: '1px solid #d1d5db', borderRadius: 4 }} />
            </label>
            <label style={{ fontSize: 13 }}>
              Center Lng
              <input type="number" step="any" value={centerLng} onChange={e => setCenterLng(e.target.value)} required
                style={{ display: 'block', width: '100%', padding: '4px 6px', marginTop: 2, border: '1px solid #d1d5db', borderRadius: 4 }} />
            </label>
            <label style={{ fontSize: 13 }}>
              Zoom (1–20)
              <input type="number" min={1} max={20} value={zoom} onChange={e => setZoom(e.target.value)} required
                style={{ display: 'block', width: '100%', padding: '4px 6px', marginTop: 2, border: '1px solid #d1d5db', borderRadius: 4 }} />
            </label>
          </div>

          <div style={{ marginBottom: 8 }}>
            <strong style={{ fontSize: 13 }}>Antennas</strong>
            {antennas.map((ant, idx) => (
              <div key={idx} style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 6 }}>
                <input placeholder="Name" value={ant.name} onChange={e => updateAntenna(idx, 'name', e.target.value)}
                  style={{ flex: 2, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 4, fontSize: 12 }} />
                <input type="number" step="any" placeholder="Lat" value={ant.lat} onChange={e => updateAntenna(idx, 'lat', e.target.value)}
                  style={{ flex: 1, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 4, fontSize: 12 }} />
                <input type="number" step="any" placeholder="Lng" value={ant.lng} onChange={e => updateAntenna(idx, 'lng', e.target.value)}
                  style={{ flex: 1, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 4, fontSize: 12 }} />
                <button type="button" onClick={() => removeAntenna(idx)} disabled={antennas.length <= 1}
                  style={{ padding: '4px 8px', background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 4, cursor: antennas.length <= 1 ? 'not-allowed' : 'pointer', fontSize: 12 }}>
                  ✕
                </button>
              </div>
            ))}
            <button type="button" onClick={addAntenna}
              style={{ marginTop: 8, padding: '4px 10px', background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer', fontSize: 12 }}>
              + Add Antenna
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
            <button type="submit" disabled={status === 'saving'}
              style={{ padding: '6px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
              {status === 'saving' ? 'Saving...' : 'Save Configuration'}
            </button>
            <button type="button" onClick={() => setOpen(false)}
              style={{ padding: '6px 14px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
              ← Back
            </button>
            {status === 'success' && <span style={{ color: '#16a34a', fontSize: 13 }}>✓ Saved</span>}
            {status === 'error' && <span style={{ color: '#dc2626', fontSize: 13 }}>{errorMsg}</span>}
          </div>
        </form>
      )}
    </div>
  )
}
