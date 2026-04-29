interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  simulated?: boolean
  highlight?: 'good' | 'warn' | 'bad' | 'neutral'
}

const HIGHLIGHT_COLORS: Record<string, string> = {
  good: '#dcfce7',
  warn: '#fef9c3',
  bad: '#fee2e2',
  neutral: '#f9fafb',
}

export function MetricCard({ label, value, unit, simulated, highlight = 'neutral' }: MetricCardProps) {
  return (
    <div style={{
      background: HIGHLIGHT_COLORS[highlight],
      border: '1px solid #e5e7eb',
      borderRadius: 8,
      padding: '12px 16px',
      minWidth: 0,
    }}>
      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
        <span>{label}</span>
        {simulated && (
          <span style={{ fontSize: 10, color: '#9ca3af', fontStyle: 'italic' }}>simulated</span>
        )}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#111827' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span style={{ fontSize: 13, fontWeight: 400, color: '#6b7280', marginLeft: 4 }}>{unit}</span>}
      </div>
    </div>
  )
}
