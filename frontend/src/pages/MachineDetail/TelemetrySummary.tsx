import type { TelemetryRecord } from '../../types/api.types'

interface Props { records: TelemetryRecord[] }

export function TelemetrySummary({ records }: Props) {
  return (
    <div>
      <h4>Telemetry</h4>
      {records.length === 0 && <p style={{ color: '#6b7280' }}>No telemetry data</p>}
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <tbody>
          {records.map(r => (
            <tr key={r.sensorType} style={{ borderBottom: '1px solid #e5e7eb' }}>
              <td style={{ padding: '4px 8px', fontWeight: 600 }}>{r.sensorType}</td>
              <td style={{ padding: '4px 8px' }}>{r.normalizedValue.toFixed(2)} {r.canonicalUnit}</td>
              <td style={{ padding: '4px 8px', color: '#9ca3af', fontSize: 12 }}>{new Date(r.timestamp).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
