import { useState, useCallback, useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { getZones, createZone, updateZone, deleteZone } from '../../api/zones'
import { getMapConfig } from '../../api/mapConfig'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Zone, MapConfig } from '../../types/api.types'
import { usePermissions } from '../../context/PermissionsContext'

const ZONE_TYPES = [
  { value: 'weighbridge',     label: 'Weighbridge',     color: '#8b5cf6' },
  { value: 'fuel_station',    label: 'Fuel Station',    color: '#f59e0b' },
  { value: 'workshop',        label: 'Workshop',        color: '#6b7280' },
  { value: 'stockpile',       label: 'Stockpile',       color: '#d97706' },
  { value: 'dump_zone',       label: 'Dump Zone',       color: '#ef4444' },
  { value: 'loading_zone',    label: 'Loading Zone',    color: '#10b981' },
  { value: 'crusher_station', label: 'Crusher Station', color: '#dc2626' },
  { value: 'general',         label: 'General',         color: '#3b82f6' },
]

const SHAPES = [
  { value: 'circle',    label: '⬤ Circle' },
  { value: 'rectangle', label: '▬ Rectangle' },
  { value: 'polygon',   label: '⬡ Polygon' },
]

const EDIT_ROLES = ['dispatcher', 'admin', 'dev']
const DELETE_ROLES = ['admin', 'dev']

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256 } },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

function getTypeColor(zone_type: string | null): string {
  return ZONE_TYPES.find(t => t.value === zone_type)?.color ?? '#3b82f6'
}

function buildZoneGeoJSON(zone: Zone): GeoJSON.Feature | null {
  const color = zone.color ?? '#3b82f6'
  if (zone.shape === 'circle' && zone.center_lat != null && zone.center_lng != null && zone.radius_meters != null) {
    const pts = 64
    const coords: [number, number][] = []
    for (let i = 0; i <= pts; i++) {
      const a = (i / pts) * 2 * Math.PI
      const dx = (zone.radius_meters / 111320) * Math.cos(a)
      const dy = (zone.radius_meters / (111320 * Math.cos(zone.center_lat * Math.PI / 180))) * Math.sin(a)
      coords.push([zone.center_lng + dy, zone.center_lat + dx])
    }
    return { type: 'Feature', properties: { color, name: zone.name }, geometry: { type: 'Polygon', coordinates: [coords] } }
  }
  if ((zone.shape === 'rectangle' || zone.shape === 'polygon') && zone.polygon_points && zone.polygon_points.length >= 3) {
    const coords: [number, number][] = zone.polygon_points.map(p => [p.lng, p.lat])
    coords.push(coords[0]) // close
    return { type: 'Feature', properties: { color, name: zone.name }, geometry: { type: 'Polygon', coordinates: [coords] } }
  }
  return null
}

export function ZonesPage() {
  const { canDo } = usePermissions()
  const canEdit = canDo('zones.create')
  const canDelete = canDo('zones.delete')

  const [zones, setZones] = useState<Zone[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [mapConfig, setMapConfig] = useState<MapConfig | null>(null)
  const [search, setSearch] = useState('')

  // Form state
  const [form, setForm] = useState({ name: '', description: '', zone_type: 'general', shape: 'circle', center_lat: '', center_lng: '', radius_meters: '200' })
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState('')

  // Interactive drawing state
  const [drawMode, setDrawMode] = useState(false)
  const [drawPoints, setDrawPoints] = useState<Array<{ lat: number; lng: number }>>([])
  const [rectStart, setRectStart] = useState<{ lat: number; lng: number } | null>(null)

  // Edit state
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<typeof form>({ name: '', description: '', zone_type: 'general', shape: 'circle', center_lat: '', center_lng: '', radius_meters: '200' })
  const [editPolygonPoints, setEditPolygonPoints] = useState<Array<{ lat: number; lng: number }>>([])
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const drawMarkersRef = useRef<maplibregl.Marker[]>([])
  const antennaMarkersRef = useRef<maplibregl.Marker[]>([])

  const load = useCallback(async () => {
    try {
      const [data, cfg] = await Promise.all([getZones(), getMapConfig().catch(() => null)])
      setZones(data)
      if (cfg) setMapConfig(cfg)
      setError(null)
    } catch (e) { setError(e) }
    finally { setLoading(false) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { load() }, [load])

  // Init map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current || !mapConfig) return
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: OSM_STYLE,
      center: [mapConfig.center_lng, mapConfig.center_lat],
      zoom: mapConfig.default_zoom,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-left')
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapConfig])

  // Render antennas
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapConfig) return
    antennaMarkersRef.current.forEach(m => m.remove())
    antennaMarkersRef.current = []
    mapConfig.antennas.forEach(ant => {
      const el = document.createElement('div')
      el.style.cssText = 'width:24px;height:24px;background:#0d9488;border:2px solid #fff;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 4px rgba(0,0,0,0.3);cursor:default;'
      el.textContent = '📡'
      el.title = ant.name
      const marker = new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([ant.lng, ant.lat]).addTo(map)
      antennaMarkersRef.current.push(marker)
    })
  }, [mapConfig])

  // Render existing zones on map
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const render = () => {
      // Remove old zone layers
      map.getStyle()?.layers?.forEach(l => {
        if (l.id.startsWith('zf-') || l.id.startsWith('zb-')) map.removeLayer(l.id)
      })
      Object.keys(map.getStyle()?.sources ?? {}).forEach(id => {
        if (id.startsWith('zs-')) map.removeSource(id)
      })
      zones.forEach(zone => {
        const feature = buildZoneGeoJSON(zone)
        if (!feature) return
        const color = zone.color ?? '#3b82f6'
        const sid = `zs-${zone.id}`
        if (!map.getSource(sid)) {
          map.addSource(sid, { type: 'geojson', data: feature })
          map.addLayer({ id: `zf-${zone.id}`, type: 'fill', source: sid, paint: { 'fill-color': color, 'fill-opacity': 0.18 } })
          map.addLayer({ id: `zb-${zone.id}`, type: 'line', source: sid, paint: { 'line-color': color, 'line-width': 2 } })
        }
      })
    }
    if (map.isStyleLoaded()) render()
    else map.once('load', render)
  }, [zones])

  // Map click for drawing
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const handler = (e: maplibregl.MapMouseEvent) => {
      if (!drawMode) return
      const { lat, lng } = e.lngLat
      const pt = { lat: parseFloat(lat.toFixed(6)), lng: parseFloat(lng.toFixed(6)) }

      if (form.shape === 'circle') {
        // First click = center
        setForm(f => ({ ...f, center_lat: pt.lat.toString(), center_lng: pt.lng.toString() }))
        setDrawPoints([pt])
        setDrawMode(false)
      } else if (form.shape === 'rectangle') {
        if (!rectStart) {
          setRectStart(pt)
          setDrawPoints([pt])
        } else {
          // Second click = opposite corner → build 4-point rectangle
          const rect = [
            rectStart,
            { lat: rectStart.lat, lng: pt.lng },
            pt,
            { lat: pt.lat, lng: rectStart.lng },
          ]
          setDrawPoints(rect)
          setRectStart(null)
          setDrawMode(false)
        }
      } else {
        // Polygon — accumulate points
        setDrawPoints(prev => [...prev, pt])
      }
    }
    map.on('click', handler)
    map.getCanvas().style.cursor = drawMode ? 'crosshair' : ''
    return () => { map.off('click', handler) }
  }, [drawMode, form.shape, rectStart])

  // Render draw markers + preview
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    drawMarkersRef.current.forEach(m => m.remove())
    drawMarkersRef.current = []
    if (map.getLayer('draw-preview')) map.removeLayer('draw-preview')
    if (map.getSource('draw-src')) map.removeSource('draw-src')

    const color = getTypeColor(form.zone_type)
    drawPoints.forEach((pt, idx) => {
      const el = document.createElement('div')
      el.style.cssText = `width:12px;height:12px;background:${color};border:2px solid #fff;border-radius:50%;`
      el.title = `Point ${idx + 1}`
      drawMarkersRef.current.push(new maplibregl.Marker({ element: el }).setLngLat([pt.lng, pt.lat]).addTo(map))
    })

    if (form.shape === 'circle' && drawPoints.length === 1 && form.radius_meters) {
      const center = drawPoints[0]
      const r = parseFloat(form.radius_meters) || 200
      const pts = 64
      const coords: [number, number][] = []
      for (let i = 0; i <= pts; i++) {
        const a = (i / pts) * 2 * Math.PI
        const dx = (r / 111320) * Math.cos(a)
        const dy = (r / (111320 * Math.cos(center.lat * Math.PI / 180))) * Math.sin(a)
        coords.push([center.lng + dy, center.lat + dx])
      }
      if (map.isStyleLoaded()) {
        map.addSource('draw-src', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [coords] } } })
        map.addLayer({ id: 'draw-preview', type: 'fill', source: 'draw-src', paint: { 'fill-color': color, 'fill-opacity': 0.25 } })
      }
    } else if (drawPoints.length >= 3) {
      const coords: [number, number][] = drawPoints.map(p => [p.lng, p.lat])
      coords.push(coords[0])
      if (map.isStyleLoaded()) {
        map.addSource('draw-src', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [coords] } } })
        map.addLayer({ id: 'draw-preview', type: 'fill', source: 'draw-src', paint: { 'fill-color': color, 'fill-opacity': 0.25 } })
      }
    }
  }, [drawPoints, form.shape, form.zone_type, form.radius_meters])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    setAdding(true); setAddError('')
    try {
      const color = getTypeColor(form.zone_type)
      const isCircle = form.shape === 'circle'
      await createZone({
        name: form.name.trim(),
        description: form.description || undefined,
        zone_type: form.zone_type,
        color,
        shape: form.shape,
        center_lat: isCircle && form.center_lat ? parseFloat(form.center_lat) : undefined,
        center_lng: isCircle && form.center_lng ? parseFloat(form.center_lng) : undefined,
        radius_meters: isCircle ? parseFloat(form.radius_meters) || 200 : undefined,
        polygon_points: !isCircle && drawPoints.length >= 3 ? drawPoints : undefined,
      })
      setForm({ name: '', description: '', zone_type: 'general', shape: 'circle', center_lat: '', center_lng: '', radius_meters: '200' })
      setDrawPoints([])
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
      shape: zone.shape ?? 'circle',
      center_lat: zone.center_lat?.toString() ?? '',
      center_lng: zone.center_lng?.toString() ?? '',
      radius_meters: zone.radius_meters?.toString() ?? '200',
    })
    setEditPolygonPoints(zone.polygon_points ?? [])
  }

  const handleSave = async () => {
    if (!editId) return
    setSaving(true)
    try {
      const isCircle = editForm.shape === 'circle'
      await updateZone(editId, {
        name: editForm.name,
        description: editForm.description || undefined,
        zone_type: editForm.zone_type,
        color: getTypeColor(editForm.zone_type),
        shape: editForm.shape,
        center_lat: isCircle && editForm.center_lat ? parseFloat(editForm.center_lat) : undefined,
        center_lng: isCircle && editForm.center_lng ? parseFloat(editForm.center_lng) : undefined,
        radius_meters: isCircle ? parseFloat(editForm.radius_meters) || 200 : undefined,
        polygon_points: !isCircle && editPolygonPoints.length >= 3 ? editPolygonPoints : undefined,
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

  const inputStyle = { display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13 } as const

  const drawInstruction = form.shape === 'circle'
    ? 'Click map to set center'
    : form.shape === 'rectangle'
    ? rectStart ? 'Click opposite corner' : 'Click first corner'
    : `Click to add points (${drawPoints.length} added, min 3)`

  return (
    <div>
      <h2>Zones</h2>
      <ErrorBanner error={error} />

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, marginBottom: 24 }}>
        {/* Left: form + list */}
        <div style={{ overflowY: 'auto', maxHeight: 700 }}>
          {canEdit && (
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 14, marginBottom: 16 }}>
              <h4 style={{ margin: '0 0 10px' }}>Create Zone</h4>
              <form onSubmit={handleAdd}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
                  <label style={{ fontSize: 13 }}>Name *<input required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} style={inputStyle} /></label>
                  <label style={{ fontSize: 13 }}>Type
                    <select value={form.zone_type} onChange={e => setForm(f => ({ ...f, zone_type: e.target.value }))} style={inputStyle}>
                      {ZONE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </label>
                </div>

                {/* Shape selector */}
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 13, marginBottom: 4 }}>Shape</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {SHAPES.map(s => (
                      <button key={s.value} type="button" onClick={() => { setForm(f => ({ ...f, shape: s.value })); setDrawPoints([]); setRectStart(null) }}
                        style={{ flex: 1, padding: '5px 4px', fontSize: 12, border: '1px solid', borderColor: form.shape === s.value ? '#2563eb' : '#d1d5db', background: form.shape === s.value ? '#eff6ff' : '#fff', borderRadius: 4, cursor: 'pointer', fontWeight: form.shape === s.value ? 700 : 400 }}>
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Circle fields */}
                {form.shape === 'circle' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 8 }}>
                    <label style={{ fontSize: 12 }}>Lat<input type="number" step="any" value={form.center_lat} onChange={e => setForm(f => ({ ...f, center_lat: e.target.value }))} style={inputStyle} /></label>
                    <label style={{ fontSize: 12 }}>Lng<input type="number" step="any" value={form.center_lng} onChange={e => setForm(f => ({ ...f, center_lng: e.target.value }))} style={inputStyle} /></label>
                    <label style={{ fontSize: 12 }}>Radius (m)<input type="number" min={10} value={form.radius_meters} onChange={e => setForm(f => ({ ...f, radius_meters: e.target.value }))} style={inputStyle} /></label>
                  </div>
                )}

                {/* Polygon/rectangle points display */}
                {form.shape !== 'circle' && drawPoints.length > 0 && (
                  <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, background: '#f3f4f6', padding: 6, borderRadius: 4 }}>
                    {drawPoints.map((p, i) => <div key={i}>P{i + 1}: {p.lat.toFixed(5)}, {p.lng.toFixed(5)}</div>)}
                    <button type="button" onClick={() => setDrawPoints(prev => prev.slice(0, -1))} style={{ marginTop: 4, fontSize: 11, padding: '2px 6px', background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 3, cursor: 'pointer' }}>↩ Undo</button>
                  </div>
                )}

                <label style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>Description<input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} style={inputStyle} /></label>

                {/* Map draw button */}
                <button type="button" onClick={() => { setDrawPoints([]); setRectStart(null); setDrawMode(true) }}
                  style={{ width: '100%', padding: '5px', fontSize: 12, background: drawMode ? '#fef3c7' : '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer', marginBottom: 8 }}>
                  {drawMode ? `📍 ${drawInstruction}` : '🗺 Draw on Map'}
                </button>
                {drawMode && (
                  <button type="button" onClick={() => { setDrawMode(false); setRectStart(null) }} style={{ width: '100%', padding: '4px', fontSize: 11, background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer', marginBottom: 8 }}>✕ Cancel Drawing</button>
                )}

                {addError && <p style={{ color: '#dc2626', fontSize: 12, margin: '0 0 6px' }}>{addError}</p>}
                <button type="submit" disabled={adding} style={{ width: '100%', padding: '6px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
                  {adding ? 'Creating...' : '+ Create Zone'}
                </button>
              </form>
            </div>
          )}

          {loading && <p style={{ color: '#6b7280' }}>Loading...</p>}

          <input
            placeholder="Search zones..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: 12, marginBottom: 8, boxSizing: 'border-box' }}
          />

          {zones.filter(z =>
            z.name.toLowerCase().includes(search.toLowerCase()) ||
            (z.zone_type ?? '').toLowerCase().includes(search.toLowerCase()) ||
            (z.description ?? '').toLowerCase().includes(search.toLowerCase())
          ).map(zone => (
            <div key={zone.id} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, marginBottom: 8, background: '#fff' }}>
              {editId === zone.id ? (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 8 }}>
                    <label style={{ fontSize: 12 }}>Name<input value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} style={inputStyle} /></label>
                    <label style={{ fontSize: 12 }}>Type
                      <select value={editForm.zone_type} onChange={e => setEditForm(f => ({ ...f, zone_type: e.target.value }))} style={inputStyle}>
                        {ZONE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                    </label>
                    <label style={{ fontSize: 12 }}>Shape
                      <select value={editForm.shape} onChange={e => setEditForm(f => ({ ...f, shape: e.target.value }))} style={inputStyle}>
                        {SHAPES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                      </select>
                    </label>
                    {editForm.shape === 'circle' && <>
                      <label style={{ fontSize: 12 }}>Lat<input type="number" step="any" value={editForm.center_lat} onChange={e => setEditForm(f => ({ ...f, center_lat: e.target.value }))} style={inputStyle} /></label>
                      <label style={{ fontSize: 12 }}>Lng<input type="number" step="any" value={editForm.center_lng} onChange={e => setEditForm(f => ({ ...f, center_lng: e.target.value }))} style={inputStyle} /></label>
                      <label style={{ fontSize: 12 }}>Radius (m)<input type="number" min={10} value={editForm.radius_meters} onChange={e => setEditForm(f => ({ ...f, radius_meters: e.target.value }))} style={inputStyle} /></label>
                    </>}
                    <label style={{ fontSize: 12, gridColumn: '1/-1' }}>Description<input value={editForm.description} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} style={inputStyle} /></label>
                  </div>
                  {/* Polygon/rectangle point editor */}
                  {editForm.shape !== 'circle' && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Points ({editPolygonPoints.length})</div>
                      <div style={{ maxHeight: 160, overflowY: 'auto', marginBottom: 6 }}>
                        {editPolygonPoints.map((pt, idx) => (
                          <div key={idx} style={{ display: 'flex', gap: 4, marginBottom: 4, alignItems: 'center' }}>
                            <span style={{ fontSize: 11, color: '#6b7280', width: 16 }}>{idx + 1}</span>
                            <input type="number" step="any" value={pt.lat}
                              onChange={e => setEditPolygonPoints(prev => prev.map((p, i) => i === idx ? { ...p, lat: parseFloat(e.target.value) || p.lat } : p))}
                              style={{ flex: 1, padding: '2px 4px', border: '1px solid #d1d5db', borderRadius: 3, fontSize: 11 }} />
                            <input type="number" step="any" value={pt.lng}
                              onChange={e => setEditPolygonPoints(prev => prev.map((p, i) => i === idx ? { ...p, lng: parseFloat(e.target.value) || p.lng } : p))}
                              style={{ flex: 1, padding: '2px 4px', border: '1px solid #d1d5db', borderRadius: 3, fontSize: 11 }} />
                            <button onClick={() => setEditPolygonPoints(prev => prev.filter((_, i) => i !== idx))}
                              style={{ padding: '1px 5px', fontSize: 10, background: '#fee2e2', border: 'none', borderRadius: 3, cursor: 'pointer' }}>✕</button>
                          </div>
                        ))}
                      </div>
                      <button type="button" onClick={() => setEditPolygonPoints(prev => [...prev, { lat: 0, lng: 0 }])}
                        style={{ fontSize: 11, padding: '3px 8px', background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 3, cursor: 'pointer' }}>
                        + Add Point
                      </button>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={handleSave} disabled={saving} style={{ flex: 1, padding: '4px', fontSize: 12, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>{saving ? '...' : 'Save'}</button>
                    <button onClick={() => setEditId(null)} style={{ padding: '4px 10px', fontSize: 12, background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer' }}>Cancel</button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 10, height: 10, borderRadius: '50%', background: zone.color ?? '#3b82f6', display: 'inline-block' }} />
                      <strong style={{ fontSize: 13 }}>{zone.name}</strong>
                      {zone.zone_type && <span style={{ fontSize: 10, background: '#f3f4f6', padding: '1px 5px', borderRadius: 3, color: '#6b7280' }}>{zone.zone_type.replace('_', ' ')}</span>}
                      {zone.shape && <span style={{ fontSize: 10, background: '#eff6ff', padding: '1px 5px', borderRadius: 3, color: '#1d4ed8' }}>{zone.shape}</span>}
                    </div>
                    {zone.description && <p style={{ margin: '3px 0 0', fontSize: 12, color: '#374151' }}>{zone.description}</p>}
                    {zone.shape === 'circle' && zone.center_lat != null && (
                      <p style={{ margin: '2px 0 0', fontSize: 11, color: '#9ca3af', fontFamily: 'monospace' }}>{zone.center_lat.toFixed(5)}, {zone.center_lng?.toFixed(5)} · r={zone.radius_meters}m</p>
                    )}
                    {zone.shape !== 'circle' && zone.polygon_points && (
                      <p style={{ margin: '2px 0 0', fontSize: 11, color: '#9ca3af' }}>{zone.polygon_points.length} points</p>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {canEdit && <button onClick={() => startEdit(zone)} style={{ padding: '2px 8px', fontSize: 11, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 3, cursor: 'pointer' }}>Edit</button>}
                    {canDelete && <button onClick={() => handleDelete(zone.id)} disabled={deletingId === zone.id} style={{ padding: '2px 8px', fontSize: 11, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 3, cursor: 'pointer' }}>{deletingId === zone.id ? '...' : 'Del'}</button>}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Map */}
        <div style={{ height: 700, borderRadius: 8, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          {mapConfig
            ? <div ref={mapContainerRef} style={{ height: '100%', width: '100%' }} />
            : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>Configure map first</div>
          }
        </div>
      </div>
    </div>
  )
}
