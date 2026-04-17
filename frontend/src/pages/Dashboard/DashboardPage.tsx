import { usePolling } from '../../hooks/usePolling'
import { getMachines } from '../../api/machines'
import { MachineCard } from './MachineCard'
import { ErrorBanner } from '../../components/ErrorBanner'

export function DashboardPage() {
  const { data: machines, error } = usePolling(getMachines, 7000)

  return (
    <div>
      <h2>Dashboard</h2>
      <ErrorBanner error={error} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16, marginTop: 16 }}>
        {machines?.map(m => <MachineCard key={m.id} machine={m} />)}
      </div>
    </div>
  )
}
