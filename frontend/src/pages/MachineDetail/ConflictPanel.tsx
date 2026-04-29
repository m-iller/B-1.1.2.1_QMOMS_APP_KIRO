import { useState } from 'react'
import type { Conflict } from '../../types/api.types'
import { resolveConflict } from '../../api/machines'
import { useAuth } from '../../context/AuthContext'

interface Props {
  machineId: string
  conflicts: Conflict[]
  onResolved: () => void
}

const RESOLVE_ROLES = ['dispatcher', 'admin', 'dev']

export function ConflictPanel({ machineId, conflicts, onResolved }: Props) {
  const { user } = useAuth()
  const canResolve = RESOLVE_ROLES.includes(user?.role ?? '')
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [error, setError] = useState('')

  if (conflicts.length === 0) return null

  const handleResolve = async (conflictId: string) => {
    setResolvingId(conflictId)
    setError('')
    try {
      await resolveConflict(machineId, conflictId)
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <div style={{ fontSize: 13 }}>
              <div style={{ marginBottom: 4 }}>
                <span style={{ color: '#6b7280' }}>Dispatcher set:</span>{' '}
                <strong style={{ color: '#1d4ed8' }}>{conflict.dispatcher_state}</strong>
                <span style={{ margin: '0 8px', color: '#9ca3af' }}>vs</span>
                <span style={{ color: '#6b7280' }}>Operator set:</span>{' '}
                <strong style={{ color: '#dc2626' }}>{conflict.operator_state}</strong>
              </div>
              <div style={{ fontSize: 11, color: '#9ca3af' }}>
                {new Date(conflict.created_at).toLocaleString()}
              </div>
            </div>
            {canResolve && (
              <button
                onClick={() => handleResolve(conflict.id)}
                disabled={resolvingId === conflict.id}
                style={{
                  padding: '5px 14px',
                  fontSize: 12,
                  background: '#1d4ed8',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: resolvingId === conflict.id ? 'not-allowed' : 'pointer',
                  flexShrink: 0,
                }}
              >
                {resolvingId === conflict.id ? 'Resolving...' : 'Resolve (Keep Dispatcher)'}
              </button>
            )}
          </div>
        </div>
      ))}

      {error && <p style={{ color: '#dc2626', fontSize: 12, margin: '8px 0 0' }}>{error}</p>}
      <p style={{ fontSize: 11, color: '#92400e', margin: '8px 0 0' }}>
        Resolving accepts the dispatcher state as authoritative and clears the conflict.
      </p>
    </div>
  )
}
