import { useNavigate } from 'react-router-dom'
import type { Machine } from '../../types/api.types'

interface Props { machine: Machine; scale?: number }

export function MachineMarker({ machine, scale = 1 }: Props) {
  const navigate = useNavigate()
  const x = (machine.posX ?? 50) * scale
  const y = (machine.posY ?? 50) * scale

  return (
    <div
      onClick={() => navigate(`/machines/${machine.id}`)}
      title={machine.name}
      style={{
        position: 'absolute', left: x, top: y,
        width: 16, height: 16, borderRadius: '50%',
        background: machine.conflictActive ? '#f59e0b' : '#2563eb',
        border: '2px solid #fff', cursor: 'pointer',
        transform: 'translate(-50%, -50%)',
      }}
    />
  )
}
