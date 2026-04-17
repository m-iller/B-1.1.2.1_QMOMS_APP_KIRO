import { useNavigate } from 'react-router-dom'
import type { Machine } from '../../types/api.types'
import { ConflictBadge } from '../../components/ConflictBadge'

const STATE_COLORS: Record<string, string> = {
  idle: '#6b7280',
  operating: '#16a34a',
  maintenance: '#d97706',
  breakdown: '#dc2626',
}

interface Props { machine: Machine }

export function MachineCard({ machine }: Props) {
  const navigate = useNavigate()
  return (
    <div
      onClick={() => navigate(`/machines/${machine.id}`)}
      style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, cursor: 'pointer', background: machine.conflictActive ? '#fff7ed' : '#fff' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>{machine.name}</strong>
        {machine.conflictActive && <ConflictBadge />}
      </div>
      <div style={{ color: '#6b7280', fontSize: 13, marginTop: 4 }}>{machine.type}</div>
      <div style={{ marginTop: 8, fontWeight: 600, color: STATE_COLORS[machine.currentState] || '#374151' }}>
        {machine.currentState.toUpperCase()}
      </div>
    </div>
  )
}
