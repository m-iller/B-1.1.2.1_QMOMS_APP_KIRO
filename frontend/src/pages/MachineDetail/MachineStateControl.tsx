import { useState } from 'react'
import { updateMachineState } from '../../api/machines'
import { usePermissions } from '../../context/PermissionsContext'

interface Props {
  machineId: string
  currentState: string
  onRefresh: () => void
}

const MACHINE_STATES = ['idle', 'operating', 'maintenance', 'breakdown']

const STATE_COLORS: Record<string, string> = {
  idle: '#f3f4f6',
  operating: '#dcfce7',
  maintenance: '#fef9c3',
  breakdown: '#fee2e2',
}

export function MachineStateControl({ machineId, currentState, onRefresh }: Props) {
  const { canDo } = usePermissions()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!canDo('machines.edit_state')) return null

  const handleChange = async (newState: string) => {
    if (newState === currentState) return
    setLoading(true)
    setError('')
    try {
      await updateMachineState(machineId, newState)
      onRefresh()
    } catch (err: any) {
      setError(err?.response?.data?.message ?? 'Failed to update state')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ marginBottom: 12 }}>
      <strong style={{ fontSize: 13 }}>Change State:</strong>
      <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
        {MACHINE_STATES.map(state => (
          <button
            key={state}
            onClick={() => handleChange(state)}
            disabled={loading || state === currentState}
            style={{
              padding: '4px 12px',
              fontSize: 12,
              borderRadius: 4,
              border: state === currentState ? '2px solid #374151' : '1px solid #d1d5db',
              background: STATE_COLORS[state] ?? '#f9fafb',
              cursor: state === currentState || loading ? 'default' : 'pointer',
              fontWeight: state === currentState ? 700 : 400,
            }}
          >
            {state}
          </button>
        ))}
      </div>
      {error && <p style={{ color: '#dc2626', fontSize: 12, marginTop: 4 }}>{error}</p>}
    </div>
  )
}
