import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { useNavigate } from 'react-router-dom'
import type { Machine, MapConfig, Zone, MachineRoute } from '../../types/api.types'

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

const SAT_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Tiles © Esri',
    },
  },
  layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }],
}

interface Props {
  machines: Machine[]
  mapConfig: MapConfig
  zones?: Zone[]
  routes?: MachineRoute[]
}

export function QuarryMap({ machines, mapConfig, zones = [], routes = [] }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const machineMarkersRef = useRef<Map<string, maplibregl.Marker>>(new Map())
  const antennaMarkersRef = useRef<maplibregl.Marker[]>([])
  const [useSatellite, setUseSatellite] = useState(false)
  const navigate = useNavigate()
  const isFirstRender = useRef(true)

  // Refs to hold latest zones/routes so style-reload handler can access them
  const zonesRef = useRef(zones)
  const routesRef = useRef(routes)
  useEffect(() => { zonesRef.current = zones }, [zones])
  useEffect(() => { routesRef.current = routes }, [routes])

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: [mapConfig.center_lng, mapConfig.center_lat],
      zoom: mapConfig.default_zoom,
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-left')
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left')
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Toggle tile layer — re-add all data layers after style reloads
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    // Skip on first render — map initializes with OSM already
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    map.setStyle(useSatellite ? SAT_STYLE : OSM_STYLE)
    // After setStyle, all sources/layers are wiped — re-add on next idle
    map.once('styledata', () => {
      // Re-add zones
      const zones = zonesRef.current
      zones.forEach(zone => {
        let coords: [number, number][] = []
        if ((zone.shape === 'rectangle' || zone.shape === 'polygon') && zone.polygon_points && zone.polygon_points.length >= 3) {
          coords = zone.polygon_points.map(p => [p.lng, p.lat] as [number, number])
          coords.push(coords[0])
        } else if (zone.center_lat != null && zone.center_lng != null && zone.radius_meters != null) {
          const pts = 64
          for (let i = 0; i <= pts; i++) {
            const angle = (i / pts) * 2 * Math.PI
            const dx = (zone.radius_meters / 111320) * Math.cos(angle)
            const dy = (zone.radius_meters / (111320 * Math.cos(zone.center_lat * Math.PI / 180))) * Math.sin(angle)
            coords.push([zone.center_lng + dy, zone.center_lat + dx])
          }
        } else return
        const color = zone.color ?? '#3b82f6'
        const sourceId = `zone-${zone.id}`
        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, { type: 'geojson', data: { type: 'Feature', properties: { id: zone.id, name: zone.name, zone_type: zone.zone_type ?? 'general', shape: zone.shape ?? 'circle', color, description: zone.description ?? '', radius_meters: zone.radius_meters ?? null, point_count: zone.polygon_points?.length ?? null }, geometry: { type: 'Polygon', coordinates: [coords] } } })
          map.addLayer({ id: `zone-fill-${zone.id}`, type: 'fill', source: sourceId, paint: { 'fill-color': color, 'fill-opacity': 0.15 } })
          map.addLayer({ id: `zone-border-${zone.id}`, type: 'line', source: sourceId, paint: { 'line-color': color, 'line-width': 2 } })
          map.on('click', `zone-fill-${zone.id}`, (e) => {
            const props = e.features?.[0]?.properties
            if (!props) return
            const shapeInfo = props.shape === 'circle' ? `<div style="font-size:12px;color:#6b7280">Radius: ${props.radius_meters}m</div>` : `<div style="font-size:12px;color:#6b7280">${props.point_count} points</div>`
            new maplibregl.Popup({ offset: 8 }).setLngLat(e.lngLat).setHTML(`<div style="min-width:160px;font-family:system-ui,sans-serif"><div style="display:flex;align-items:center;gap:6px;margin-bottom:4px"><span style="width:10px;height:10px;border-radius:50%;background:${props.color};display:inline-block;flex-shrink:0"></span><strong style="font-size:14px">${props.name}</strong></div><div style="font-size:11px;background:#f3f4f6;padding:2px 6px;border-radius:3px;display:inline-block;margin-bottom:4px">${(props.zone_type ?? 'general').replace('_', ' ')} · ${props.shape}</div>${shapeInfo}${props.description ? `<div style="font-size:12px;color:#374151;margin-top:4px">${props.description}</div>` : ''}</div>`).addTo(map)
          })
          map.on('mouseenter', `zone-fill-${zone.id}`, () => { map.getCanvas().style.cursor = 'pointer' })
          map.on('mouseleave', `zone-fill-${zone.id}`, () => { map.getCanvas().style.cursor = '' })
        }
      })
      // Re-add routes
      const routes = routesRef.current
      routes.forEach(route => {
        if (route.waypoints.length < 2) return
        const coords = route.waypoints.map(wp => [wp.lng, wp.lat])
        const srcId = `route-src-${route.id}`
        if (!map.getSource(srcId)) {
          map.addSource(srcId, { type: 'geojson', data: { type: 'Feature', properties: { id: route.id, name: route.name, color: route.color, waypoint_count: route.waypoints.length }, geometry: { type: 'LineString', coordinates: coords } } })
          map.addLayer({ id: `route-line-${route.id}`, type: 'line', source: srcId, paint: { 'line-color': route.color, 'line-width': 3 } })
          map.on('click', `route-line-${route.id}`, (e) => {
            const props = e.features?.[0]?.properties
            if (!props) return
            new maplibregl.Popup({ offset: 8 }).setLngLat(e.lngLat).setHTML(`<div style="min-width:150px;font-family:system-ui,sans-serif"><div style="display:flex;align-items:center;gap:6px;margin-bottom:6px"><span style="width:14px;height:4px;background:${props.color};border-radius:2px;display:inline-block;flex-shrink:0"></span><strong style="font-size:14px">${props.name}</strong></div><div style="font-size:12px;color:#6b7280">${props.waypoint_count} waypoints</div></div>`).addTo(map)
          })
          map.on('mouseenter', `route-line-${route.id}`, () => { map.getCanvas().style.cursor = 'pointer' })
          map.on('mouseleave', `route-line-${route.id}`, () => { map.getCanvas().style.cursor = '' })
        }
      })
    })
  }, [useSatellite])

  // Update machine markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const visibleMachines = machines.filter(
      m => m.pos_x !== null && m.pos_y !== null
    )
    const currentIds = new Set(visibleMachines.map(m => m.id))
    // Only remove markers for machines that are no longer in the machines list at all
    // (not just temporarily missing position — position may lag a poll cycle)
    const allMachineIds = new Set(machines.map(m => m.id))
    machineMarkersRef.current.forEach((marker, id) => {
      if (!allMachineIds.has(id)) {
        marker.remove()
        machineMarkersRef.current.delete(id)
      }
    })

    // Add or update markers
    visibleMachines.forEach(machine => {
      const lng = machine.pos_x!
      const lat = machine.pos_y!
      const isConflict = machine.conflict_active
      const color = isConflict ? '#f59e0b' : '#2563eb'

      const existing = machineMarkersRef.current.get(machine.id)
      if (existing) {
        // Update position
        existing.setLngLat([lng, lat])
        // Update color via element
        const el = existing.getElement()
        const dot = el.querySelector('.machine-dot') as HTMLElement | null
        if (dot) dot.style.background = color
      } else {
        // Create new marker
        const el = document.createElement('div')
        el.className = `machine-marker ${isConflict ? 'marker-conflict' : 'marker-default'}`
        el.style.cssText = 'cursor:pointer;'

        const dot = document.createElement('div')
        dot.className = 'machine-dot'
        dot.style.cssText = `
          width: 20px; height: 20px;
          background: ${color};
          border: 2px solid #fff;
          border-radius: 50%;
          box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        `
        el.appendChild(dot)

        // Popup content
        const popupHtml = `
          <div style="min-width:150px;font-family:system-ui,sans-serif">
            <strong style="font-size:14px">${machine.name}</strong>
            <div style="color:#6b7280;font-size:12px;margin-top:2px">${machine.type}</div>
            <div style="margin-top:6px;font-size:13px">State: <strong>${machine.current_state}</strong></div>
            ${isConflict ? '<div style="color:#d97706;font-size:12px;margin-top:2px">⚠ Conflict active</div>' : ''}
            <div style="color:#9ca3af;font-size:11px;margin-top:4px;font-family:monospace">
              ${lat.toFixed(5)}, ${lng.toFixed(5)}
            </div>
            <button
              onclick="window.__navigateToMachine('${machine.id}')"
              style="margin-top:8px;padding:4px 10px;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px;width:100%"
            >View Details</button>
          </div>
        `

        const popup = new maplibregl.Popup({ offset: 14 }).setHTML(popupHtml)
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([lng, lat])
          .setPopup(popup)
          .addTo(map)

        machineMarkersRef.current.set(machine.id, marker)
      }
    })
  }, [machines])

  // Expose navigate for popup button clicks
  useEffect(() => {
    (window as any).__navigateToMachine = (id: string) => navigate(`/machines/${id}`)
    return () => { delete (window as any).__navigateToMachine }
  }, [navigate])

  // Add antenna markers once (they don't move)
  useEffect(() => {    const map = mapRef.current
    if (!map) return

    // Remove old antenna markers
    antennaMarkersRef.current.forEach(m => m.remove())
    antennaMarkersRef.current = []

    mapConfig.antennas.forEach(antenna => {
      // Single root element — no wrapper div, no position:relative parent
      const el = document.createElement('div')
      el.className = 'antenna-marker'
      el.style.cssText = `
        position: relative;
        width: 30px;
        height: 30px;
        background: #0d9488;
        border: 2px solid #fff;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        cursor: default;
      `
      el.textContent = '📡'
      el.title = antenna.name

      // Label positioned above the icon via absolute, inside the same root element
      const label = document.createElement('div')
      label.style.cssText = `
        position: absolute;
        bottom: 34px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.72);
        color: #fff;
        font-size: 11px;
        font-weight: 600;
        font-family: system-ui, sans-serif;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
        pointer-events: none;
        line-height: 1.4;
      `
      label.textContent = antenna.name
      el.appendChild(label)

      // anchor: 'center' — MapLibre pins the center of el to the coordinate
      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([antenna.lng, antenna.lat])
        .addTo(map)

      antennaMarkersRef.current.push(marker)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapConfig.antennas])

  // Render zone circles
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const addLayers = () => {
      map.getStyle()?.layers?.forEach(layer => {
        if (layer.id.startsWith('zone-fill-') || layer.id.startsWith('zone-border-')) {
          map.removeLayer(layer.id)
        }
      })
      Object.keys(map.getStyle()?.sources ?? {}).forEach(id => {
        if (id.startsWith('zone-')) map.removeSource(id)
      })

      zones.forEach(zone => {
        let coords: [number, number][] = []

        if ((zone.shape === 'rectangle' || zone.shape === 'polygon') && zone.polygon_points && zone.polygon_points.length >= 3) {
          coords = zone.polygon_points.map(p => [p.lng, p.lat] as [number, number])
          coords.push(coords[0])
        } else if (zone.center_lat != null && zone.center_lng != null && zone.radius_meters != null) {
          const pts = 64
          for (let i = 0; i <= pts; i++) {
            const angle = (i / pts) * 2 * Math.PI
            const dx = (zone.radius_meters / 111320) * Math.cos(angle)
            const dy = (zone.radius_meters / (111320 * Math.cos(zone.center_lat * Math.PI / 180))) * Math.sin(angle)
            coords.push([zone.center_lng + dy, zone.center_lat + dx])
          }
        } else {
          return
        }

        const color = zone.color ?? '#3b82f6'
        const sourceId = `zone-${zone.id}`
        const properties = {
          id: zone.id,
          name: zone.name,
          zone_type: zone.zone_type ?? 'general',
          shape: zone.shape ?? 'circle',
          color,
          description: zone.description ?? '',
          radius_meters: zone.radius_meters ?? null,
          point_count: zone.polygon_points?.length ?? null,
        }

        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, {
            type: 'geojson',
            data: { type: 'Feature', properties, geometry: { type: 'Polygon', coordinates: [coords] } },
          })
          map.addLayer({ id: `zone-fill-${zone.id}`, type: 'fill', source: sourceId, paint: { 'fill-color': color, 'fill-opacity': 0.15 } })
          map.addLayer({ id: `zone-border-${zone.id}`, type: 'line', source: sourceId, paint: { 'line-color': color, 'line-width': 2 } })

          // Click on fill layer → popup
          map.on('click', `zone-fill-${zone.id}`, (e) => {
            const props = e.features?.[0]?.properties
            if (!props) return
            const shapeInfo = props.shape === 'circle'
              ? `<div style="font-size:12px;color:#6b7280">Radius: ${props.radius_meters}m</div>`
              : `<div style="font-size:12px;color:#6b7280">${props.point_count} points</div>`
            new maplibregl.Popup({ offset: 8 })
              .setLngLat(e.lngLat)
              .setHTML(`
                <div style="min-width:160px;font-family:system-ui,sans-serif">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
                    <span style="width:10px;height:10px;border-radius:50%;background:${props.color};display:inline-block;flex-shrink:0"></span>
                    <strong style="font-size:14px">${props.name}</strong>
                  </div>
                  <div style="font-size:11px;background:#f3f4f6;padding:2px 6px;border-radius:3px;display:inline-block;margin-bottom:4px">${(props.zone_type ?? 'general').replace('_', ' ')} · ${props.shape}</div>
                  ${shapeInfo}
                  ${props.description ? `<div style="font-size:12px;color:#374151;margin-top:4px">${props.description}</div>` : ''}
                </div>
              `)
              .addTo(map)
          })
          map.on('mouseenter', `zone-fill-${zone.id}`, () => { map.getCanvas().style.cursor = 'pointer' })
          map.on('mouseleave', `zone-fill-${zone.id}`, () => { map.getCanvas().style.cursor = '' })
        }
      })
    }
    if (map.isStyleLoaded()) addLayers()
    else map.once('load', addLayers)
  }, [zones])

  // Render machine routes
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Track route midpoint markers for cleanup
    const routeMarkers: maplibregl.Marker[] = (map as any).__routeMarkers ?? []
    routeMarkers.forEach(m => m.remove())
    ;(map as any).__routeMarkers = []

    const addLayers = () => {
      map.getStyle()?.layers?.forEach(layer => {
        if (layer.id.startsWith('route-line-')) map.removeLayer(layer.id)
      })
      Object.keys(map.getStyle()?.sources ?? {}).forEach(id => {
        if (id.startsWith('route-src-')) map.removeSource(id)
      })

      routes.forEach(route => {
        if (route.waypoints.length < 2) return
        const coords = route.waypoints.map(wp => [wp.lng, wp.lat])
        const srcId = `route-src-${route.id}`

        if (!map.getSource(srcId)) {
          map.addSource(srcId, {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: { id: route.id, name: route.name, color: route.color, waypoint_count: route.waypoints.length },
              geometry: { type: 'LineString', coordinates: coords },
            },
          })
          map.addLayer({ id: `route-line-${route.id}`, type: 'line', source: srcId, paint: { 'line-color': route.color, 'line-width': 3 } })

          // Click on line
          map.on('click', `route-line-${route.id}`, (e) => {
            const props = e.features?.[0]?.properties
            if (!props) return
            new maplibregl.Popup({ offset: 8 })
              .setLngLat(e.lngLat)
              .setHTML(`
                <div style="min-width:150px;font-family:system-ui,sans-serif">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
                    <span style="width:14px;height:4px;background:${props.color};border-radius:2px;display:inline-block;flex-shrink:0"></span>
                    <strong style="font-size:14px">${props.name}</strong>
                  </div>
                  <div style="font-size:12px;color:#6b7280">${props.waypoint_count} waypoints</div>
                </div>
              `)
              .addTo(map)
          })
          map.on('mouseenter', `route-line-${route.id}`, () => { map.getCanvas().style.cursor = 'pointer' })
          map.on('mouseleave', `route-line-${route.id}`, () => { map.getCanvas().style.cursor = '' })
        }

        // Midpoint marker for easier clicking on thin lines
        const mid = route.waypoints[Math.floor(route.waypoints.length / 2)]
        const el = document.createElement('div')
        el.style.cssText = `width:10px;height:10px;background:${route.color};border:2px solid #fff;border-radius:50%;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.4);`
        const popup = new maplibregl.Popup({ offset: 10 }).setHTML(`
          <div style="min-width:150px;font-family:system-ui,sans-serif">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
              <span style="width:14px;height:4px;background:${route.color};border-radius:2px;display:inline-block;flex-shrink:0"></span>
              <strong style="font-size:14px">${route.name}</strong>
            </div>
            <div style="font-size:12px;color:#6b7280">${route.waypoints.length} waypoints</div>
          </div>
        `)
        const marker = new maplibregl.Marker({ element: el }).setLngLat([mid.lng, mid.lat]).setPopup(popup).addTo(map)
        ;(map as any).__routeMarkers.push(marker)
      })
    }
    if (map.isStyleLoaded()) addLayers()
    else map.once('load', addLayers)
  }, [routes])

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Layer toggle */}
      <button
        onClick={() => setUseSatellite(s => !s)}
        style={{
          position: 'absolute', top: 10, right: 10, zIndex: 10,
          padding: '6px 12px', background: '#fff',
          border: '1px solid #d1d5db', borderRadius: 6,
          cursor: 'pointer', fontSize: 13, fontWeight: 600,
          boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
        }}
      >
        {useSatellite ? '🗺 Street' : '🛰 Satellite'}
      </button>

      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
    </div>
  )
}
