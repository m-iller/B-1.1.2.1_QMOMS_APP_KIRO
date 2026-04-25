import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { useNavigate } from 'react-router-dom'
import type { Machine, MapConfig } from '../../types/api.types'

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
}

export function QuarryMap({ machines, mapConfig }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const machineMarkersRef = useRef<Map<string, maplibregl.Marker>>(new Map())
  const antennaMarkersRef = useRef<maplibregl.Marker[]>([])
  const [useSatellite, setUseSatellite] = useState(false)
  const navigate = useNavigate()

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

  // Toggle tile layer
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.setStyle(useSatellite ? SAT_STYLE : OSM_STYLE)
  }, [useSatellite])

  // Update machine markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const visibleMachines = machines.filter(
      m => m.pos_x !== null && m.pos_y !== null
    )
    const currentIds = new Set(visibleMachines.map(m => m.id))

    // Remove markers for machines no longer visible
    machineMarkersRef.current.forEach((marker, id) => {
      if (!currentIds.has(id)) {
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
  useEffect(() => {
    const map = mapRef.current
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
