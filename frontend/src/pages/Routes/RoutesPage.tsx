import { useState, useCallback, useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { getMachines } from '../../api/machines'
import { getMapConfig } from '../../api/mapConfig'
import { getZones } from '../../api/zones'
import { getAllRoutes, createRoute, updateRoute, deleteRoute } from '../../api/routes'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Machine, MachineRoute, MapConfig, Waypoint, Zone } from '../../types/api.types'

const ROUTE_COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256 } },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

function buildZoneGeoJSON(zone: Zone): GeoJSON.Feature | null {
  if (zone.shape === 'circle' && zone.center_lat != null && zone.center_lng != null && zone.radius_meters != null) {
    const pts = 48
    const coords: [number, number][] = []
    for (let i = 0; i <= pts; i++) {
      const a = (i / pts) * 2 * Math.PI
      const dx = (zone.radius_meters / 111320) * Math.cos(a)
      const dy = (zone.radius_meters / (111320 * Math.cos(zone.center_lat * Math.PI / 180))) * Math.sin(a)
      coords.push([zone.center_lng + dy, zone.center_lat + dx])
    }
    return { type: 'Feature', properties: { color: zone.color ?? '#3b82f6', name: zone.name }, geometry: { type: 'Polygon', coordinates: [coords] } }
  }
  if (zone.polygon_points && zone.polygon_points.length >= 3) {
    const coords: [number, number][] = zone.polygon_points.map(p => [p.lng, p.lat])
    coords.push(coords[0])
    return { type: 'Feature', properties: { color: zone.color ?? '#3b82f6', name: zone.name }, geometry: { type: 'Polygon', coordinates: [coords] } }
  }
  return null
}

export function RoutesPage() {
  const [machines, setMachines] = useState<Machine[]>([])
  const [routes, setRoutes] = useState<MachineRoute[]>([])
  const [zones, setZones] = useState<Zone[]>([])
  const [mapConfig, setMapConfig] = useState<MapConfig | null>(null)
  const [error, setError] = useState<unknown>(null)

  const [selectedMachineId, setSelectedMachineId] = useState('')
  const [editingRoute, setEditingRoute] = useState<MachineRoute | null>(null)
  const [routeName, setRouteName] = useState('Route')
  const [routeColor, setRouteColor] = useState(ROUTE_COLORS[0])
  const [waypoints, setWaypoints] = useState<Waypoint[]>([])
  const [pickingMode, setPickingMode] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Manual coordinate entry
  const [manualLat, setManualLat] = useState('')
  const [manualLng, setManualLng] = useState('')

  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const waypointMarkersRef = useRef<maplibregl.Marker[]>([])
  const antennaMarkersRef = useRef<maplibregl.Marker[]>([])

  const load = useCallback(async () => {
    try {
      const [m, r, cfg, z] = await Promise.all([getMachines(), getAllRoutes(), getMapConfig().catch(() => null), getZones()])
      setMachines(m); setRoutes(r); setZones(z)
      if (cfg) setMapConfig(cfg)
    } catch (e) { setError(e) }
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
      el.textContent = '📡'; el.title = ant.name
      antennaMarkersRef.current.push(new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([ant.lng, ant.lat]).addTo(map))
    })
  }, [mapConfig])

  // Render zones
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const render = () => {
      map.getStyle()?.layers?.forEach(l => { if (l.id.startsWith('rzf-') || l.id.startsWith('rzb-')) map.removeLayer(l.id) })
      Object.keys(map.getStyle()?.sources ?? {}).forEach(id => { if (id.startsWith('rzs-')) map.removeSource(id) })
      zones.forEach(zone => {
        const feature = buildZoneGeoJSON(zone)
        if (!feature) return
        const color = zone.color ?? '#3b82f6'
        const sid = `rzs-${zone.id}`
        if (!map.getSource(sid)) {
          map.addSource(sid, { type: 'geojson', data: feature })
          map.addLayer({ id: `rzf-${zone.id}`, type: 'fill', source: sid, paint: { 'fill-color': color, 'fill-opacity': 0.12 } })
          map.addLayer({ id: `rzb-${zone.id}`, type: 'line', source: sid, paint: { 'line-color': color, 'line-width': 1.5, 'line-dasharray': [3, 2] } })
        }
      })
    }
    if (map.isStyleLoaded()) render()
    else map.once('load', render)
  }, [zones])

  // Map click for waypoints
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const handler = (e: maplibregl.MapMouseEvent) => {
      if (!pickingMode) return
      const { lat, lng } = e.lngLat
      setWaypoints(prev => [...prev, { lat: parseFloat(lat.toFixed(6)), lng: parseFloat(lng.toFixed(6)) }])
    }
    map.on('click', handler)
    map.getCanvas().style.cursor = pickingMode ? 'crosshair' : ''
    return () => { map.off('click', handler) }
  }, [pickingMode])

  // Render waypoint markers + preview line
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    waypointMarkersRef.current.forEach(m => m.remove())
    waypointMarkersRef.current = []
    if (map.getLayer('edit-line')) map.removeLayer('edit-line')
    if (map.getSource('edit-src')) map.removeSource('edit-src')

    waypoints.forEach((wp, idx) => {
      const el = document.createElement('div')
      el.style.cssText = `width:16px;height:16px;background:${routeColor};border:2px solid #fff;border-radius:50%;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,0.4);`
      el.title = `${idx + 1}: ${wp.lat}, ${wp.lng}`
      waypointMarkersRef.current.push(new maplibregl.Marker({ element: el }).setLngLat([wp.lng, wp.lat]).addTo(map))
    })

    if (waypoints.length >= 2 && map.isStyleLoaded()) {
      const coords = waypoints.map(wp => [wp.lng, wp.lat])
      map.addSource('edit-src', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: coords } } })
      map.addLayer({ id: 'edit-line', type: 'line', source: 'edit-src', paint: { 'line-color': routeColor, 'line-width': 3, 'line-dasharray': [2, 1] } })
    }
  }, [waypoints, routeColor])

  // Render saved routes
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const render = () => {
      map.getStyle()?.layers?.forEach(l => { if (l.id.startsWith('rl-')) map.removeLayer(l.id) })
      Object.keys(map.getStyle()?.sources ?? {}).forEach(id => { if (id.startsWith('rs-')) map.removeSource(id) })
      const visible = selectedMachineId ? routes.filter(r => r.machine_id === selectedMachineId) : routes
      visible.forEach(route => {
        if (route.waypoints.length < 2) return
        const coords = route.waypoints.map((wp: Waypoint) => [wp.lng, wp.lat])
        const sid = `rs-${route.id}`
        if (!map.getSource(sid)) {
          map.addSource(sid, { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: coords } } })
          map.addLayer({ id: `rl-${route.id}`, type: 'line', source: sid, paint: { 'line-color': route.color, 'line-width': 3 } })
        }
      })
    }
    if (map.isStyleLoaded()) render()
    else map.once('load', render)
  }, [routes, selectedMachineId])

  const startNew = () => { setEditingRoute(null); setWaypoints([]); setRouteName('Route'); setRouteColor(ROUTE_COLORS[0]); setPickingMode(true) }
  const startEdit = (r: MachineRoute) => { setEditingRoute(r); setWaypoints(r.waypoints); setRouteName(r.name); setRouteColor(r.color); setPickingMode(true) }

  const handleSave = async () => {
    if (!selectedMachineId || waypoints.length < 2) return
    setSaving(true)
    try {
      if (editingRoute) await updateRoute(editingRoute.id, { name: routeName, waypoints, color: routeColor })
      else await createRoute({ machine_id: selectedMachineId, name: routeName, waypoints, color: routeColor })
      setPickingMode(false); setWaypoints([]); setEditingRoute(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try { await deleteRoute(id); await load() }
    finally { setDeletingId(null) }
  }

  const addManualPoint = () => {
    const lat = parseFloat(manualLat)
    const lng = parseFloat(manualLng)
    if (isNaN(lat) || isNaN(lng)) return
    setWaypoints(prev => [...prev, { lat: parseFloat(lat.toFixed(6)), lng: parseFloat(lng.toFixed(6)) }])
    setManualLat(''); setManualLng('')
  }

  const machineRoutes = routes.filter(r => r.machine_id === selectedMachineId)

  return (
    <div>
      <h2>Machine Routes</h2>
      <ErrorBanner error={error} />

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>
        {/* Left panel */}
        <div style={{ overflowY: 'auto', maxHeight: 700, paddingRight: 4 }}>
          <label style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
            Machine
            <select value={selectedMachineId} onChange={e => { setSelectedMachineId(e.target.value); setPickingMode(false); setWaypoints([]) }}
              style={{ display: 'block', width: '100%', padding: '6px 8px', marginTop: 4, border: '1px solid #d1d5db', borderRadius: 4 }}>
              <option value="">— All —</option>
              {machines.map(m => <option key={m.id} value={m.id}>{m.name} ({m.type})</option>)}
            </select>
          </label>

          {selectedMachineId && (
            <button onClick={startNew} style={{ width: '100%', padding: '7px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, marginBottom: 12 }}>
              + New Route
            </button>
          )}

          {machineRoutes.map(route => (
            <div key={route.id} style={{ border: '1px solid #e5e7eb', borderRadius: 6, padding: 10, marginBottom: 8, background: '#fff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <span style={{ width: 10, height: 10, background: route.color, borderRadius: 2, flexShrink: 0 }} />
                <strong style={{ fontSize: 13 }}>{route.name}</strong>
              </div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>{route.waypoints.length} waypoints</div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={() => startEdit(route)} style={{ flex: 1, padding: '3px', fontSize: 11, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer' }}>Edit</button>
                <button onClick={() => handleDelete(route.id)} disabled={deletingId === route.id} style={{ flex: 1, padding: '3px', fontSize: 11, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>{deletingId === route.id ? '...' : 'Delete'}</button>
              </div>
            </div>
          ))}

          {/* Edit panel */}
          {pickingMode && selectedMachineId && (
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: 12, marginTop: 8 }}>
              <p style={{ fontSize: 12, color: '#166534', margin: '0 0 8px', fontWeight: 600 }}>📍 Click map to add waypoints</p>

              <label style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                Name<input value={routeName} onChange={e => setRouteName(e.target.value)} style={{ display: 'block', width: '100%', padding: '4px 6px', marginTop: 2, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 12 }} />
              </label>

              <div style={{ display: 'flex', gap: 5, marginBottom: 8 }}>
                {ROUTE_COLORS.map(c => (
                  <div key={c} onClick={() => setRouteColor(c)} style={{ width: 18, height: 18, background: c, borderRadius: 3, cursor: 'pointer', border: c === routeColor ? '2px solid #111' : '2px solid transparent' }} />
                ))}
              </div>

              {/* Waypoint table */}
              {waypoints.length > 0 && (
                <div style={{ marginBottom: 8, maxHeight: 160, overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                    <thead><tr style={{ background: '#f3f4f6' }}>
                      <th style={{ padding: '2px 4px', textAlign: 'left' }}>#</th>
                      <th style={{ padding: '2px 4px', textAlign: 'left' }}>Lat</th>
                      <th style={{ padding: '2px 4px', textAlign: 'left' }}>Lng</th>
                      <th />
                    </tr></thead>
                    <tbody>
                      {waypoints.map((wp, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                          <td style={{ padding: '2px 4px', color: '#6b7280' }}>{idx + 1}</td>
                          <td style={{ padding: '2px 4px', fontFamily: 'monospace' }}>
                            <input type="number" step="any" value={wp.lat} onChange={e => setWaypoints(prev => prev.map((w, i) => i === idx ? { ...w, lat: parseFloat(e.target.value) || w.lat } : w))}
                              style={{ width: 80, padding: '1px 3px', border: '1px solid #d1d5db', borderRadius: 3, fontSize: 11 }} />
                          </td>
                          <td style={{ padding: '2px 4px', fontFamily: 'monospace' }}>
                            <input type="number" step="any" value={wp.lng} onChange={e => setWaypoints(prev => prev.map((w, i) => i === idx ? { ...w, lng: parseFloat(e.target.value) || w.lng } : w))}
                              style={{ width: 80, padding: '1px 3px', border: '1px solid #d1d5db', borderRadius: 3, fontSize: 11 }} />
                          </td>
                          <td><button onClick={() => setWaypoints(prev => prev.filter((_, i) => i !== idx))} style={{ padding: '1px 5px', fontSize: 10, background: '#fee2e2', border: 'none', borderRadius: 3, cursor: 'pointer' }}>✕</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Manual add */}
              <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
                <input type="number" step="any" placeholder="Lat" value={manualLat} onChange={e => setManualLat(e.target.value)}
                  style={{ flex: 1, minWidth: 0, padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 4, fontSize: 11 }} />
                <input type="number" step="any" placeholder="Lng" value={manualLng} onChange={e => setManualLng(e.target.value)}
                  style={{ flex: 1, minWidth: 0, padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 4, fontSize: 11 }} />
                <button onClick={addManualPoint} style={{ padding: '3px 8px', fontSize: 11, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer', flexShrink: 0 }}>+ Add</button>
              </div>

              <div style={{ display: 'flex', gap: 5, flexWrap: 'nowrap' }}>
                <button onClick={handleSave} disabled={saving || waypoints.length < 2} style={{ flex: 1, padding: '5px', fontSize: 12, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: waypoints.length < 2 ? 'not-allowed' : 'pointer', minWidth: 0 }}>
                  {saving ? '...' : 'Save Route'}
                </button>
                <button onClick={() => setWaypoints(prev => prev.slice(0, -1))} disabled={waypoints.length === 0} style={{ padding: '5px 7px', fontSize: 12, background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 4, cursor: 'pointer', flexShrink: 0 }}>↩</button>
                <button onClick={() => { setPickingMode(false); setWaypoints([]) }} style={{ padding: '5px 7px', fontSize: 12, background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer', flexShrink: 0 }}>✕</button>
              </div>
            </div>
          )}
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
