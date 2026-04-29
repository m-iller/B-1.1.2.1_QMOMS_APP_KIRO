interface MetricSectionProps {
  title: string
  children: React.ReactNode
}

export function MetricSection({ title, children }: MetricSectionProps) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 600, color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: 6 }}>
        {title}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
        {children}
      </div>
    </div>
  )
}
