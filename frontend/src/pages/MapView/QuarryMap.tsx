import 'leaflet/dist/leaflet.css'
import { useState } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'
import type { Machine, MapConfig } from '../../types/api.types'
import { MachineMarkerLeaflet } from './MachineMarkerLeaflet'
import { AntennaMarkerLeaflet } from './AntennaMarkerLeaflet'

const OSM_TILE = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const SAT_TILE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const SAT_ATTRIBUTION = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'

interface Props {
  machines: Machine[]
  mapConfig: MapConfig
}

export function QuarryMap({ machines, mapConfig }: Props) {
  const [useSatellite, setUseSatellite] = useState(false)

  const visibleMachines = machines.filter(
    m => m.pos_x !== null && m.pos_y !== null
  )

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Layer toggle button */}
      <button
        onClick={() => setUseSatellite(s => !s)}
        style={{
          position: 'absolute',
          top: 10,
          right: 10,
          zIndex: 1000,
          padding: '6px 12px',
          background: '#fff',
          border: '1px solid #d1d5db',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 600,
          boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
        }}
      >
        {useSatellite ? '🗺 Street' : '🛰 Satellite'}
      </button>

      <MapContainer
        center={[mapConfig.center_lat, mapConfig.center_lng]}
        zoom={mapConfig.default_zoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url={useSatellite ? SAT_TILE : OSM_TILE}
          attribution={useSatellite ? SAT_ATTRIBUTION : OSM_ATTRIBUTION}
        />

        {visibleMachines.map(machine => (
          <MachineMarkerLeaflet key={machine.id} machine={machine} />
        ))}

        {mapConfig.antennas.map((antenna, idx) => (
          <AntennaMarkerLeaflet key={`${antenna.name}-${idx}`} antenna={antenna} />
        ))}
      </MapContainer>
    </div>
  )
}
