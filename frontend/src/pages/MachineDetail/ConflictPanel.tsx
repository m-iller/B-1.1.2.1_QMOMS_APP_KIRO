import { useState } from 'react'
import type { Conflict } from '../../types/api.types'
import { resolveConflict } from '../../api/machines'
import { usePermissions } from '../../context/PermissionsContext'

interface Props {
  machineId: string
  conflicts: Conflict[]
  onResolved: () => void
}

type Resolution = 'dispatcher' | 'operator'

export function ConflictPanel({ machineId, conflicts, onResolved }: Props) {
  const { canDo } = usePermissions()
  const canResolve = canDo('conflicts.resolve')
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [error, setError] = useState('')

  if (conflicts.length === 0) return null

  const handleResolve = async (conflictId: string, resolution: Resolution) => {
    setResolvingId(`${conflictId}-${resolution}`)
    setError('')
    try {
      await resolveConflict(machineId, conflictId, resolution)
      onResolved()
    } catch (err: any) {
      setError(err?.response?.data?.message ?? 'Failed to resolve conflict')
    } finally {
      setResolvingId(null)
    }
  }

  return (
    <div style={{
      background: '#fef3c7',
      border: '1px solid #f59e0b',
      borderRadius: 8,
      padding: 16,
      marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 18 }}>⚠️</span>
        <strong style={{ color: '#92400e' }}>
          {conflicts.length} Active Conflict{conflicts.length > 1 ? 's' : ''}
        </strong>
      </div>

      {conflicts.map(conflict => (
        <div
          key={conflict.id}
          style={{
            background: '#fff',
            border: '1px solid #fcd34d',
            borderRadius: 6,
            padding: 12,
            marginBottom: 8,
          }}
        >
          <div style={{ fontSize: 13, marginBottom: 10 }}>
            <div style={{ marginBottom: 6 }}>
              <span style={{ color: '#6b7280' }}>Dispatcher set:</span>{' '}
              <strong style={{ color: '#1d4ed8' }}>{conflict.dispatcher_state}</strong>
              <span style={{ margin: '0 10px', color: '#9ca3af' }}>vs</span>
              <span style={{ color: '#6b7280' }}>Operator set:</span>{' '}
              <strong style={{ color: '#dc2626' }}>{conflict.operator_state}</strong>
            </div>
            <div style={{ fontSize: 11, color: '#9ca3af' }}>
              {new Date(conflict.created_at).toLocaleString()}
            </div>
          </div>

          {canResolve && (
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => handleResolve(conflict.id, 'dispatcher')}
                disabled={resolvingId !== null}
                style={{
                  padding: '5px 14px',
                  fontSize: 12,
                  background: '#1d4ed8',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: resolvingId !== null ? 'not-allowed' : 'pointer',
                }}
              >
                {resolvingId === `${conflict.id}-dispatcher` ? '...' : `✓ Keep Dispatcher (${conflict.dispatcher_state})`}
              </button>
              <button
                onClick={() => handleResolve(conflict.id, 'operator')}
                disabled={resolvingId !== null}
                style={{
                  padding: '5px 14px',
                  fontSize: 12,
                  background: '#dc2626',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: resolvingId !== null ? 'not-allowed' : 'pointer',
                }}
              >
                {resolvingId === `${conflict.id}-operator` ? '...' : `✓ Keep Operator (${conflict.operator_state})`}
              </button>
            </div>
          )}
        </div>
      ))}

      {error && <p style={{ color: '#dc2626', fontSize: 12, margin: '8px 0 0' }}>{error}</p>}
    </div>
  )
}
