import { usePolling } from '../../hooks/usePolling'
import { getMachines } from '../../api/machines'
import { getMapConfig } from '../../api/mapConfig'
import { QuarryMap } from './QuarryMap'
import { MapConfigForm } from './MapConfigForm'
import { ErrorBanner } from '../../components/ErrorBanner'

export function MapViewPage() {
  const { data: machines, error: machinesError } = usePolling(getMachines, 7000)
  const { data: mapConfig, error: mapConfigError } = usePolling(getMapConfig, 7000)

  const isNotConfigured = (mapConfigError as any)?.response?.status === 404

  return (
    <div>
      <h2>Map View</h2>
      <ErrorBanner error={machinesError} />
      {!isNotConfigured && <ErrorBanner error={mapConfigError} />}

      <div style={{ height: '600px', width: '100%', borderRadius: 8, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
        {mapConfig ? (
          <QuarryMap machines={machines ?? []} mapConfig={mapConfig} />
        ) : isNotConfigured ? (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f9fafb',
            color: '#6b7280',
            flexDirection: 'column',
            gap: 8,
          }}>
            <span style={{ fontSize: 32 }}>🗺</span>
            <p style={{ margin: 0, fontWeight: 600 }}>No map configured</p>
            <p style={{ margin: 0, fontSize: 13 }}>Open settings below to configure the map.</p>
          </div>
        ) : (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9fafb', color: '#9ca3af' }}>
            Loading map...
          </div>
        )}
      </div>

      <MapConfigForm />
    </div>
  )
}
