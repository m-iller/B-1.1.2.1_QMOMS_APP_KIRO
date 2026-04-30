import { useState, useCallback, useEffect } from 'react'
import { getZones, createZone, updateZone, deleteZone } from '../../api/zones'
import { getMapConfig } from '../../api/mapConfig'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Zone } from '../../types/api.types'
import { useAuth } from '../../context/AuthContext'

const ZONE_TYPES = [
  { value: 'weighbridge',     label: 'Weighbridge',      color: '#8b5cf6' },
  { value: 'fuel_station',    label: 'Fuel Station',     color: '#f59e0b' },
  { value: 'workshop',        label: 'Workshop',         color: '#6b7280' },
  { value: 'stockpile',       label: 'Stockpile',        color: '#d97706' },
  { value: 'dump_zone',       label: 'Dump Zone',        color: '#ef4444' },
  { value: 'loading_zone',    label: 'Loading Zone',     color: '#10b981' },
  { value: 'crusher_station', label: 'Crusher Station',  color: '#dc2626' },
  { value: 'general',         label: 'General',          color: '#3b82f6' },
]

const EDIT_ROLES = ['dispatcher', 'admin', 'dev']
const DELETE_ROLES = ['admin', 'dev']

function getTypeColor(zone_type: string | null): string {
  return ZONE_TYPES.find(t => t.value === zone_type)?.color ?? '#3b82f6'
}

export function ZonesPage() {
  const { user } = useAuth()
  const canEdit = EDIT_ROLES.includes(user?.role ?? '')
  const canDelete = DELETE_ROLES.includes(user?.role ?? '')

  const [zones, setZones] = useState<Zone[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number } | null>(null)

  // Add form
  const [form, setForm] = useState({
    name: '', description: '', zone_type: 'general',
    center_lat: '', center_lng: '', radius_meters: '200',
  })
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState('')

  // Edit state
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<typeof form>({ name: '', description: '', zone_type: 'general', center_lat: '', center_lng: '', radius_meters: '200' })
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [data, cfg] = await Promise.all([getZones(), getMapConfig().catch(() => null)])
      setZones(data)
      if (cfg) setMapCenter({ lat: cfg.center_lat, lng: cfg.center_lng })
      setError(null)
    } catch (e) { setError(e) }
    finally { setLoading(false) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { load() }, [load])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    setAdding(true); setAddError('')
    try {
      const color = getTypeColor(form.zone_type)
      await createZone({
        name: form.name.trim(),
        description: form.description || undefined,
        zone_type: form.zone_type,
        color,
        center_lat: form.center_lat ? parseFloat(form.center_lat) : mapCenter?.lat,
        center_lng: form.center_lng ? parseFloat(form.center_lng) : mapCenter?.lng,
        radius_meters: parseFloat(form.radius_meters) || 200,
      })
      setForm({ name: '', description: '', zone_type: 'general', center_lat: '', center_lng: '', radius_meters: '200' })
      await load()
    } catch (err: any) {
      setAddError(err?.response?.data?.message ?? 'Failed to create zone')
    } finally { setAdding(false) }
  }

  const startEdit = (zone: Zone) => {
    setEditId(zone.id)
    setEditForm({
      name: zone.name,
      description: zone.description ?? '',
      zone_type: zone.zone_type ?? 'general',
      center_lat: zone.center_lat?.toString() ?? '',
      center_lng: zone.center_lng?.toString() ?? '',
      radius_meters: zone.radius_meters?.toString() ?? '200',
    })
  }

  const handleSave = async () => {
    if (!editId) return
    setSaving(true)
    try {
      await updateZone(editId, {
        name: editForm.name,
        description: editForm.description || undefined,
        zone_type: editForm.zone_type,
        color: getTypeColor(editForm.zone_type),
        center_lat: editForm.center_lat ? parseFloat(editForm.center_lat) : undefined,
        center_lng: editForm.center_lng ? parseFloat(editForm.center_lng) : undefined,
        radius_meters: parseFloat(editForm.radius_meters) || 200,
      })
      setEditId(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try { await deleteZone(id); await load() }
    catch (err: any) { alert(err?.response?.data?.message ?? 'Failed to delete zone') }
    finally { setDeletingId(null) }
  }

  const inputStyle = { display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13 }

  return (
    <div>
      <h2>Zones</h2>
      <ErrorBanner error={error} />

      {canEdit && (
        <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 24 }}>
          <h4 style={{ margin: '0 0 12px' }}>Create Zone</h4>
          {mapCenter && <p style={{ fontSize: 12, color: '#6b7280', margin: '0 0 8px' }}>Map center: {mapCenter.lat.toFixed(5)}, {mapCenter.lng.toFixed(5)} — used as default position if left blank</p>}
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <label style={{ fontSize: 13 }}>Name *<input required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} style={inputStyle} /></label>
              <label style={{ fontSize: 13 }}>Type
                <select value={form.zone_type} onChange={e => setForm(f => ({ ...f, zone_type: e.target.value }))} style={inputStyle}>
                  {ZONE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </label>
              <label style={{ fontSize: 13 }}>Center Lat<input type="number" step="any" value={form.center_lat} onChange={e => setForm(f => ({ ...f, center_lat: e.target.value }))} placeholder={mapCenter?.lat.toFixed(5)} style={inputStyle} /></label>
              <label style={{ fontSize: 13 }}>Center Lng<input type="number" step="any" value={form.center_lng} onChange={e => setForm(f => ({ ...f, center_lng: e.target.value }))} placeholder={mapCenter?.lng.toFixed(5)} style={inputStyle} /></label>
              <label style={{ fontSize: 13 }}>Radius (m)<input type="number" min={10} value={form.radius_meters} onChange={e => setForm(f => ({ ...f, radius_meters: e.target.value }))} style={inputStyle} /></label>
              <label style={{ fontSize: 13 }}>Description<input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} style={inputStyle} /></label>
            </div>
            {addError && <p style={{ color: '#dc2626', fontSize: 12, margin: '0 0 8px' }}>{addError}</p>}
            <button type="submit" disabled={adding} style={{ padding: '6px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
              {adding ? 'Creating...' : '+ Create Zone'}
            </button>
          </form>
        </div>
      )}

      {loading && <p style={{ color: '#6b7280' }}>Loading...</p>}

      {zones.map(zone => (
        <div key={zone.id} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 14, marginBottom: 10, background: '#fff' }}>
          {editId === zone.id ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
                <label style={{ fontSize: 13 }}>Name<input value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} style={inputStyle} /></label>
                <label style={{ fontSize: 13 }}>Type
                  <select value={editForm.zone_type} onChange={e => setEditForm(f => ({ ...f, zone_type: e.target.value }))} style={inputStyle}>
                    {ZONE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </label>
                <label style={{ fontSize: 13 }}>Center Lat<input type="number" step="any" value={editForm.center_lat} onChange={e => setEditForm(f => ({ ...f, center_lat: e.target.value }))} style={inputStyle} /></label>
                <label style={{ fontSize: 13 }}>Center Lng<input type="number" step="any" value={editForm.center_lng} onChange={e => setEditForm(f => ({ ...f, center_lng: e.target.value }))} style={inputStyle} /></label>
                <label style={{ fontSize: 13 }}>Radius (m)<input type="number" min={10} value={editForm.radius_meters} onChange={e => setEditForm(f => ({ ...f, radius_meters: e.target.value }))} style={inputStyle} /></label>
                <label style={{ fontSize: 13 }}>Description<input value={editForm.description} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} style={inputStyle} /></label>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={handleSave} disabled={saving} style={{ padding: '4px 12px', fontSize: 12, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>{saving ? 'Saving...' : 'Save'}</button>
                <button onClick={() => setEditId(null)} style={{ padding: '4px 12px', fontSize: 12, background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer' }}>Cancel</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 12, height: 12, borderRadius: '50%', background: zone.color ?? '#3b82f6', display: 'inline-block', flexShrink: 0 }} />
                  <strong>{zone.name}</strong>
                  {zone.zone_type && <span style={{ fontSize: 11, background: '#f3f4f6', padding: '1px 6px', borderRadius: 4, color: '#6b7280' }}>{zone.zone_type.replace('_', ' ')}</span>}
                </div>
                {zone.description && <p style={{ margin: '4px 0 0', fontSize: 13, color: '#374151' }}>{zone.description}</p>}
                {zone.center_lat != null && (
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: '#9ca3af', fontFamily: 'monospace' }}>
                    {zone.center_lat.toFixed(5)}, {zone.center_lng?.toFixed(5)} · r={zone.radius_meters}m
                  </p>
                )}
                <p style={{ margin: '2px 0 0', fontSize: 11, color: '#d1d5db' }}>ID: {zone.id}</p>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {canEdit && <button onClick={() => startEdit(zone)} style={{ padding: '3px 10px', fontSize: 12, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer' }}>Edit</button>}
                {canDelete && <button onClick={() => handleDelete(zone.id)} disabled={deletingId === zone.id} style={{ padding: '3px 10px', fontSize: 12, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>{deletingId === zone.id ? '...' : 'Delete'}</button>}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
