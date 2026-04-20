import L from 'leaflet'
import { Marker, Tooltip } from 'react-leaflet'
import type { AntennaDefinition } from '../../types/api.types'

const antennaIcon = L.divIcon({
  className: 'antenna-marker',
  html: `<div style="
    width: 28px;
    height: 28px;
    background: #0d9488;
    border: 2px solid #fff;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.4);
  ">📡</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

interface Props {
  antenna: AntennaDefinition
}

export function AntennaMarkerLeaflet({ antenna }: Props) {
  return (
    <Marker position={[antenna.lat, antenna.lng]} icon={antennaIcon}>
      <Tooltip permanent direction="top" offset={[0, -16]}>
        <span style={{ fontWeight: 600, fontSize: 12 }}>{antenna.name}</span>
      </Tooltip>
    </Marker>
  )
}
