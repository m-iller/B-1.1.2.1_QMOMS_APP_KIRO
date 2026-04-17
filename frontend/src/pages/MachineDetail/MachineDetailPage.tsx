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
        {machine.conflictActive && <ConflictBadge />}
      </div>
      <ErrorBanner error={machineError} />
      <p><strong>State:</strong> {machine.currentState}</p>
      <p><strong>Type:</strong> {machine.type}</p>
      {machine.currentZoneId && <p><strong>Zone:</strong> {machine.currentZoneId}</p>}
      <hr />
      <TelemetrySummary records={telemetry ?? []} />
      <hr />
      <TaskList tasks={tasks ?? []} />
    </div>
  )
}
