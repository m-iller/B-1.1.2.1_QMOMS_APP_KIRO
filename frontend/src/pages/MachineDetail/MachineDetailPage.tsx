import { useParams } from 'react-router-dom'
import { usePolling } from '../../hooks/usePolling'
import { getMachine } from '../../api/machines'
import { getLatestTelemetry } from '../../api/telemetry'
import { getTasks } from '../../api/tasks'
import { TelemetrySummary } from './TelemetrySummary'
import { TaskList } from './TaskList'
import { ConflictBadge } from '../../components/ConflictBadge'
import { ErrorBanner } from '../../components/ErrorBanner'

export function MachineDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: machine, error: machineError } = usePolling(() => getMachine(id!), 7000)
  const { data: telemetry } = usePolling(() => getLatestTelemetry(id!), 7000)
  const { data: tasks } = usePolling(() => getTasks({ machine_id: id }), 7000)

  if (!machine) return <div>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h2>{machine.name}</h2>
        {machine.conflict_active && <ConflictBadge />}
        <span style={{ fontSize: 11, color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%', background: '#16a34a',
            display: 'inline-block', animation: 'pulse 2s infinite'
          }} />
          Live
        </span>
      </div>
      <ErrorBanner error={machineError} />
      <p><strong>State:</strong> {machine.current_state}</p>
      <p><strong>Type:</strong> {machine.type}</p>
      {machine.current_zone_id && <p><strong>Zone:</strong> {machine.current_zone_id}</p>}
      {machine.pos_x !== null && machine.pos_y !== null && (
        <p>
          <strong>Position:</strong>{' '}
          <span style={{ fontFamily: 'monospace', fontSize: 13 }}>
            lat {machine.pos_y?.toFixed(6)}, lng {machine.pos_x?.toFixed(6)}
          </span>
        </p>
      )}
      <hr />
      <TelemetrySummary records={telemetry ?? []} />
      <hr />
      <TaskList tasks={tasks ?? []} />
    </div>
  )
}
