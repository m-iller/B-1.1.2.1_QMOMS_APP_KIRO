import { useState, useCallback, useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { getMachines } from '../../api/machines'
import { getMapConfig } from '../../api/mapConfig'
import { getAllRoutes, createRoute, updateRoute, deleteRoute } from '../../api/routes'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Machine, MachineRoute, MapConfig, Waypoint } from '../../types/api.types'

const ROUTE_COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256 } },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

export function RoutesPage() {
  const [machines, setMachines] = useState<Machine[]>([])
  const [routes, setRoutes] = useState<MachineRoute[]>([])
  const [mapConfig, setMapConfig] = useState<MapConfig | null>(null)
  const [error, setError] = useState<unknown>(null)

  const [selectedMachineId, setSelectedMachineId] = useState<string>('')
  const [editingRoute, setEditingRoute] = useState<MachineRoute | null>(null)
  const [newRouteName, setNewRouteName] = useState('Route')
  const [newRouteColor, setNewRouteColor] = useState(ROUTE_COLORS[0])
  const [waypoints, setWaypoints] = useState<Waypoint[]>([])
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [pickingMode, setPickingMode] = useState(false)

  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const waypointMarkersRef = useRef<maplibregl.Marker[]>([])

  const load = useCallback(async () => {
    try {
      const [m, r, cfg] = await Promise.all([getMachines(), getAllRoutes(), getMapConfig().catch(() => null)])
      setMachines(m)
      setRoutes(r)
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

  // Map click handler for picking waypoints
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const handler = (e: maplibregl.MapMouseEvent) => {
      if (!pickingMode) return
      const { lng, lat } = e.lngLat
      setWaypoints(prev => [...prev, { lat: parseFloat(lat.toFixed(6)), lng: parseFloat(lng.toFixed(6)) }])
    }
    map.on('click', handler)
    map.getCanvas().style.cursor = pickingMode ? 'crosshair' : ''
    return () => { map.off('click', handler) }
  }, [pickingMode])

  // Render waypoint markers and route line
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Clear old markers
    waypointMarkersRef.current.forEach(m => m.remove())
    waypointMarkersRef.current = []

    // Remove old route layer/source
    if (map.getLayer('edit-route-line')) map.removeLayer('edit-route-line')
    if (map.getSource('edit-route')) map.removeSource('edit-route')

    waypoints.forEach((wp, idx) => {
      const el = document.createElement('div')
      el.style.cssText = `width:16px;height:16px;background:${newRouteColor};border:2px solid #fff;border-radius:50%;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,0.4);`
      el.title = `Waypoint ${idx + 1}: ${wp.lat}, ${wp.lng}`
      const marker = new maplibregl.Marker({ element: el }).setLngLat([wp.lng, wp.lat]).addTo(map)
      waypointMarkersRef.current.push(marker)
    })

    if (waypoints.length >= 2) {
      const coords = waypoints.map(wp => [wp.lng, wp.lat])
      if (map.isStyleLoaded()) {
        map.addSource('edit-route', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: coords } } })
        map.addLayer({ id: 'edit-route-line', type: 'line', source: 'edit-route', paint: { 'line-color': newRouteColor, 'line-width': 3, 'line-dasharray': [2, 1] } })
      }
    }
  }, [waypoints, newRouteColor])

  // Render all saved routes on map
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    // Remove old route layers
    routes.forEach(r => {
      if (map.getLayer(`route-${r.id}`)) map.removeLayer(`route-${r.id}`)
      if (map.getSource(`route-${r.id}`)) map.removeSource(`route-${r.id}`)
    })

    const machineRoutes = selectedMachineId
      ? routes.filter(r => r.machine_id === selectedMachineId)
      : routes

    machineRoutes.forEach(route => {
      if (route.waypoints.length < 2) return
      const coords = route.waypoints.map((wp: Waypoint) => [wp.lng, wp.lat])
      if (!map.getSource(`route-${route.id}`)) {
        map.addSource(`route-${route.id}`, { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: coords } } })
        map.addLayer({ id: `route-${route.id}`, type: 'line', source: `route-${route.id}`, paint: { 'line-color': route.color, 'line-width': 3 } })
      }
    })
  }, [routes, selectedMachineId])

  const startNewRoute = () => {
    setEditingRoute(null)
    setWaypoints([])
    setNewRouteName('Route')
    setNewRouteColor(ROUTE_COLORS[0])
    setPickingMode(true)
  }

  const startEditRoute = (route: MachineRoute) => {
    setEditingRoute(route)
    setWaypoints(route.waypoints)
    setNewRouteName(route.name)
    setNewRouteColor(route.color)
    setPickingMode(true)
  }

  const handleSave = async () => {
    if (!selectedMachineId || waypoints.length < 2) return
    setSaving(true)
    try {
      if (editingRoute) {
        await updateRoute(editingRoute.id, { name: newRouteName, waypoints, color: newRouteColor })
      } else {
        await createRoute({ machine_id: selectedMachineId, name: newRouteName, waypoints, color: newRouteColor })
      }
      setPickingMode(false)
      setWaypoints([])
      setEditingRoute(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try { await deleteRoute(id); await load() }
    finally { setDeletingId(null) }
  }

  const machineRoutes = routes.filter(r => r.machine_id === selectedMachineId)
  const selectedMachine = machines.find(m => m.id === selectedMachineId)

  return (
    <div>
      <h2>Machine Routes</h2>
      <ErrorBanner error={error} />

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
        {/* Left panel */}
        <div>
          <label style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
            Select Machine
            <select
              value={selectedMachineId}
              onChange={e => { setSelectedMachineId(e.target.value); setPickingMode(false); setWaypoints([]) }}
              style={{ display: 'block', width: '100%', padding: '6px 8px', marginTop: 4, border: '1px solid #d1d5db', borderRadius: 4 }}
            >
              <option value="">— All machines —</option>
              {machines.map(m => <option key={m.id} value={m.id}>{m.name} ({m.type})</option>)}
            </select>
          </label>

          {selectedMachineId && (
            <>
              <button
                onClick={startNewRoute}
                style={{ width: '100%', padding: '7px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, marginBottom: 12 }}
              >
                + New Route
              </button>

              {machineRoutes.map(route => (
                <div key={route.id} style={{ border: '1px solid #e5e7eb', borderRadius: 6, padding: 10, marginBottom: 8, background: '#fff' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <span style={{ width: 10, height: 10, background: route.color, borderRadius: 2, flexShrink: 0 }} />
                    <strong style={{ fontSize: 13 }}>{route.name}</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>{route.waypoints.length} waypoints</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => startEditRoute(route)} style={{ flex: 1, padding: '3px', fontSize: 11, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer' }}>Edit</button>
                    <button onClick={() => handleDelete(route.id)} disabled={deletingId === route.id} style={{ flex: 1, padding: '3px', fontSize: 11, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>{deletingId === route.id ? '...' : 'Delete'}</button>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Edit panel */}
          {pickingMode && selectedMachineId && (
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: 12, marginTop: 12 }}>
              <p style={{ fontSize: 12, color: '#166534', margin: '0 0 8px', fontWeight: 600 }}>
                📍 Click on map to add waypoints ({waypoints.length} added)
              </p>
              <label style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                Route Name
                <input value={newRouteName} onChange={e => setNewRouteName(e.target.value)} style={{ display: 'block', width: '100%', padding: '4px 6px', marginTop: 2, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 12 }} />
              </label>
              <label style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                Color
                <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                  {ROUTE_COLORS.map(c => (
                    <div key={c} onClick={() => setNewRouteColor(c)} style={{ width: 20, height: 20, background: c, borderRadius: 4, cursor: 'pointer', border: c === newRouteColor ? '2px solid #111' : '2px solid transparent' }} />
                  ))}
                </div>
              </label>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={handleSave} disabled={saving || waypoints.length < 2} style={{ flex: 1, padding: '5px', fontSize: 12, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: waypoints.length < 2 ? 'not-allowed' : 'pointer' }}>
                  {saving ? 'Saving...' : 'Save Route'}
                </button>
                <button onClick={() => setWaypoints(prev => prev.slice(0, -1))} disabled={waypoints.length === 0} style={{ padding: '5px 8px', fontSize: 12, background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 4, cursor: 'pointer' }}>↩ Undo</button>
                <button onClick={() => { setPickingMode(false); setWaypoints([]) }} style={{ padding: '5px 8px', fontSize: 12, background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>✕</button>
              </div>
            </div>
          )}
        </div>

        {/* Map */}
        <div style={{ height: 600, borderRadius: 8, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          {mapConfig ? (
            <div ref={mapContainerRef} style={{ height: '100%', width: '100%' }} />
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>
              Configure map first to use route editor
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
