import L from 'leaflet'
import { Marker, Popup } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import type { Machine } from '../../types/api.types'

export function getMachineMarkerIcon(machine: Machine): L.DivIcon {
  const isConflict = machine.conflict_active
  const bg = isConflict ? '#f59e0b' : '#2563eb'
  const className = isConflict
    ? 'machine-marker marker-conflict'
    : 'machine-marker marker-default'
  return L.divIcon({
    className,
    html: `<div style="
      width: 20px;
      height: 20px;
      background: ${bg};
      border: 2px solid #fff;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

interface Props {
  machine: Machine
}

export function MachineMarkerLeaflet({ machine }: Props) {
  const navigate = useNavigate()

  if (machine.pos_x === null || machine.pos_y === null) return null

  return (
    <Marker
      position={[machine.pos_y, machine.pos_x]}
      icon={getMachineMarkerIcon(machine)}
    >
      <Popup>
        <div style={{ minWidth: 140 }}>
          <strong>{machine.name}</strong>
          <div style={{ color: '#6b7280', fontSize: 12, marginTop: 2 }}>{machine.type}</div>
          <div style={{ marginTop: 4, fontSize: 13 }}>
            State: <strong>{machine.current_state}</strong>
          </div>
          {machine.conflict_active && (
            <div style={{ color: '#d97706', fontSize: 12, marginTop: 2 }}>⚠ Conflict active</div>
          )}
          <button
            onClick={() => navigate(`/machines/${machine.id}`)}
            style={{
              marginTop: 8,
              padding: '4px 10px',
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 12,
              width: '100%',
            }}
          >
            View Details
          </button>
        </div>
      </Popup>
    </Marker>
  )
}
