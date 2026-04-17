import { usePolling } from '../../hooks/usePolling'
import { getMachines } from '../../api/machines'
import { MachineMarker } from './MachineMarker'
import { ErrorBanner } from '../../components/ErrorBanner'

export function MapViewPage() {
  const { data: machines, error } = usePolling(getMachines, 7000)

  return (
    <div>
      <h2>Map View</h2>
      <ErrorBanner error={error} />
      <div style={{ position: 'relative', width: 800, height: 500, background: '#d1fae5', border: '1px solid #6ee7b7', borderRadius: 8, overflow: 'hidden', marginTop: 16 }}>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280', fontSize: 14 }}>
          Quarry Layout (static background)
        </div>
        {machines?.map(m => <MachineMarker key={m.id} machine={m} />)}
      </div>
    </div>
  )
}
