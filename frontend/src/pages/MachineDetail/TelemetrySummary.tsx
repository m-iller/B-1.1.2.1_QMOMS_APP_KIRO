import type { TelemetryRecord } from '../../types/api.types'

interface Props { records: TelemetryRecord[] }

export function TelemetrySummary({ records }: Props) {
  const lastUpdate = records.length > 0
    ? new Date(Math.max(...records.map(r => new Date(r.timestamp).getTime())))
    : null

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h4 style={{ margin: 0 }}>Telemetry</h4>
        {lastUpdate && (
          <span style={{ fontSize: 11, color: '#9ca3af' }}>
            Last reading: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {records.length === 0 && (
        <p style={{ color: '#6b7280', marginTop: 8 }}>No telemetry data yet</p>
      )}

      <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: 8 }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            <th style={{ padding: '4px 8px', textAlign: 'left', fontSize: 12, color: '#6b7280', fontWeight: 600 }}>Sensor</th>
            <th style={{ padding: '4px 8px', textAlign: 'left', fontSize: 12, color: '#6b7280', fontWeight: 600 }}>Value</th>
            <th style={{ padding: '4px 8px', textAlign: 'left', fontSize: 12, color: '#6b7280', fontWeight: 600 }}>Time</th>
          </tr>
        </thead>
        <tbody>
          {records.map(r => (
            <tr key={r.sensor_type} style={{ borderBottom: '1px solid #e5e7eb' }}>
              <td style={{ padding: '6px 8px', fontWeight: 600, fontSize: 13 }}>{r.sensor_type}</td>
              <td style={{ padding: '6px 8px', fontFamily: 'monospace', fontSize: 13 }}>
                {r.normalized_value.toFixed(2)} {r.canonical_unit}
              </td>
              <td style={{ padding: '6px 8px', color: '#9ca3af', fontSize: 12 }}>
                {new Date(r.timestamp).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
