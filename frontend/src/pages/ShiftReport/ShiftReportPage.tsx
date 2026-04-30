import { useState, useRef } from 'react'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { getDailyReport, type DailyReport } from '../../api/reports'
import { ErrorBanner } from '../../components/ErrorBanner'

const STATE_COLORS: Record<string, string> = {
  operating: '#16a34a',
  idle: '#6b7280',
  maintenance: '#d97706',
  breakdown: '#dc2626',
}

export function ShiftReportPage() {
  const today = new Date().toISOString().slice(0, 10)
  const [date, setDate] = useState(today)
  const [report, setReport] = useState<DailyReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  // Manual dispatcher entries
  const [dispatcherNotes, setDispatcherNotes] = useState('')
  const [manualTonnes, setManualTonnes] = useState('')
  const [manualMachinesUsed, setManualMachinesUsed] = useState('')
  const [shiftName, setShiftName] = useState('Day Shift')
  const [dispatcherName, setDispatcherName] = useState('')
  const [incidents, setIncidents] = useState('')
  const [weatherConditions, setWeatherConditions] = useState('')

  const printRef = useRef<HTMLDivElement>(null)

  const handleLoad = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getDailyReport(date)
      setReport(data)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  const [exporting, setExporting] = useState(false)

  const handleExportPDF = async () => {
    const el = printRef.current
    if (!el) return
    setExporting(true)
    try {
      const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: '#ffffff' })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      let yOffset = 0
      let remainingHeight = imgHeight
      while (remainingHeight > 0) {
        pdf.addImage(imgData, 'PNG', 0, -yOffset, imgWidth, imgHeight)
        remainingHeight -= pageHeight
        yOffset += pageHeight
        if (remainingHeight > 0) pdf.addPage()
      }
      pdf.save(`shift-report-${date}.pdf`)
    } finally {
      setExporting(false)
    }
  }

  const totalTonnes = manualTonnes
    ? parseFloat(manualTonnes)
    : report?.haul_cycles.total_tonnes ?? 0

  const machinesUsed = manualMachinesUsed
    ? parseInt(manualMachinesUsed)
    : report?.active_machines ?? 0

  return (
    <div>
      {/* Controls — hidden when printing */}
      <div className="no-print">
        <h2>Shift Report</h2>
        <ErrorBanner error={error} />

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20, background: '#f9fafb', padding: 16, borderRadius: 8, border: '1px solid #e5e7eb' }}>
          <label style={{ fontSize: 13 }}>
            Date
            <input type="date" value={date} onChange={e => setDate(e.target.value)}
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
          <label style={{ fontSize: 13 }}>
            Shift Name
            <input value={shiftName} onChange={e => setShiftName(e.target.value)}
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
          <label style={{ fontSize: 13 }}>
            Dispatcher Name
            <input value={dispatcherName} onChange={e => setDispatcherName(e.target.value)} placeholder="Your name"
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
          <label style={{ fontSize: 13 }}>
            Weather Conditions
            <input value={weatherConditions} onChange={e => setWeatherConditions(e.target.value)} placeholder="e.g. Clear, 18°C"
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
          <label style={{ fontSize: 13 }}>
            Total Tonnes Mined (override)
            <input type="number" value={manualTonnes} onChange={e => setManualTonnes(e.target.value)} placeholder="Auto from haul cycles"
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
          <label style={{ fontSize: 13 }}>
            Machines Used (override)
            <input type="number" value={manualMachinesUsed} onChange={e => setManualMachinesUsed(e.target.value)} placeholder="Auto from data"
              style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }} />
          </label>
        </div>

        <label style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
          Incidents / Safety Notes
          <textarea value={incidents} onChange={e => setIncidents(e.target.value)} rows={2} placeholder="Any incidents, near-misses, or safety observations..."
            style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13, resize: 'vertical' }} />
        </label>

        <label style={{ fontSize: 13, display: 'block', marginBottom: 16 }}>
          Dispatcher Notes
          <textarea value={dispatcherNotes} onChange={e => setDispatcherNotes(e.target.value)} rows={3} placeholder="General observations, issues, recommendations..."
            style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13, resize: 'vertical' }} />
        </label>

        <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
          <button onClick={handleLoad} disabled={loading}
            style={{ padding: '7px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
            {loading ? 'Loading...' : '📊 Load Data'}
          </button>
          <button onClick={handleExportPDF} disabled={!report || exporting}
            style={{ padding: '7px 18px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: 6, cursor: (report && !exporting) ? 'pointer' : 'not-allowed', fontSize: 13 }}>
            {exporting ? '⏳ Generating PDF...' : '⬇ Download PDF'}
          </button>
        </div>
      </div>

      {/* Printable report */}
      {report && (
        <div ref={printRef} id="shift-report-print">
          <style>{`
            @media print {
              .no-print { display: none !important; }
              body { font-family: system-ui, sans-serif; font-size: 12px; }
              #shift-report-print { padding: 20px; }
              .page-break { page-break-before: always; }
            }
          `}</style>

          {/* Header */}
          <div style={{ borderBottom: '3px solid #1e293b', paddingBottom: 12, marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h1 style={{ margin: 0, fontSize: 22, color: '#1e293b' }}>⛏ Quarry Operations — Shift Report</h1>
                <div style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>
                  {shiftName} · {new Date(date).toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
              </div>
              <div style={{ textAlign: 'right', fontSize: 13, color: '#374151' }}>
                {dispatcherName && <div><strong>Dispatcher:</strong> {dispatcherName}</div>}
                {weatherConditions && <div><strong>Weather:</strong> {weatherConditions}</div>}
                <div style={{ color: '#9ca3af', fontSize: 11, marginTop: 4 }}>Generated: {new Date().toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <h3 style={{ margin: '0 0 10px', color: '#1e293b', fontSize: 15 }}>Key Performance Indicators</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 24 }}>
            {[
              { label: 'Total Tonnes Mined', value: `${totalTonnes.toLocaleString()} t`, color: '#dcfce7' },
              { label: 'Haul Cycles', value: `${report.haul_cycles.completed} / ${report.haul_cycles.total}`, color: '#eff6ff' },
              { label: 'Machines Active', value: `${machinesUsed} / ${report.total_machines}`, color: '#fef3c7' },
              { label: 'Tasks Completed', value: `${report.tasks.completed} / ${report.tasks.total}`, color: '#f0fdf4' },
              { label: 'Tasks Overdue', value: String(report.tasks.overdue), color: report.tasks.overdue > 0 ? '#fee2e2' : '#f9fafb' },
              { label: 'Tasks Pending', value: String(report.tasks.pending), color: '#f9fafb' },
              { label: 'Tasks In Progress', value: String(report.tasks.active), color: '#eff6ff' },
              { label: 'Notifications', value: String(report.notifications.length), color: '#f9fafb' },
            ].map(m => (
              <div key={m.label} style={{ background: m.color, border: '1px solid #e5e7eb', borderRadius: 6, padding: '10px 12px' }}>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 3 }}>{m.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#111827' }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Machine Usage */}
          <h3 style={{ margin: '0 0 10px', color: '#1e293b', fontSize: 15 }}>Machine Usage</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24, fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#1e293b', color: '#fff' }}>
                {['Machine', 'Type', 'Current State', 'Utilization %', 'State Changes'].map(h => (
                  <th key={h} style={{ padding: '7px 10px', textAlign: 'left', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {report.machines.map((m, idx) => (
                <tr key={m.id} style={{ background: idx % 2 === 0 ? '#f9fafb' : '#fff', borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '6px 10px', fontWeight: 600 }}>{m.name}</td>
                  <td style={{ padding: '6px 10px', color: '#6b7280' }}>{m.type}</td>
                  <td style={{ padding: '6px 10px' }}>
                    <span style={{ background: STATE_COLORS[m.current_state] ?? '#6b7280', color: '#fff', padding: '2px 8px', borderRadius: 10, fontSize: 11 }}>
                      {m.current_state}
                    </span>
                  </td>
                  <td style={{ padding: '6px 10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 6, background: '#e5e7eb', borderRadius: 3 }}>
                        <div style={{ width: `${m.utilization_pct}%`, height: '100%', background: m.utilization_pct > 60 ? '#16a34a' : m.utilization_pct > 30 ? '#d97706' : '#dc2626', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: 12, minWidth: 36 }}>{m.utilization_pct}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '6px 10px', color: '#6b7280' }}>{m.state_changes}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Notifications */}
          {report.notifications.length > 0 && (
            <>
              <h3 style={{ margin: '0 0 10px', color: '#1e293b', fontSize: 15 }}>Notifications ({report.notifications.length})</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24, fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f3f4f6' }}>
                    {['Time', 'Type', 'Message'].map(h => (
                      <th key={h} style={{ padding: '6px 10px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.notifications.slice(0, 30).map((n, idx) => {
                    const p = n.payload as Record<string, string>
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '5px 10px', color: '#6b7280', whiteSpace: 'nowrap' }}>
                          {new Date(n.created_at).toLocaleTimeString()}
                        </td>
                        <td style={{ padding: '5px 10px' }}>
                          <span style={{ background: n.type === 'alert' ? '#fee2e2' : '#eff6ff', color: n.type === 'alert' ? '#991b1b' : '#1d4ed8', padding: '1px 6px', borderRadius: 3, fontSize: 11 }}>
                            {n.type}
                          </span>
                        </td>
                        <td style={{ padding: '5px 10px' }}>{p.name ?? p.desc ?? JSON.stringify(p)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </>
          )}

          {/* Incidents */}
          {incidents && (
            <>
              <h3 style={{ margin: '0 0 8px', color: '#1e293b', fontSize: 15 }}>Incidents / Safety Notes</h3>
              <div style={{ background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 6, padding: 12, marginBottom: 20, fontSize: 13, whiteSpace: 'pre-wrap' }}>
                {incidents}
              </div>
            </>
          )}

          {/* Dispatcher Notes */}
          {dispatcherNotes && (
            <>
              <h3 style={{ margin: '0 0 8px', color: '#1e293b', fontSize: 15 }}>Dispatcher Notes</h3>
              <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 6, padding: 12, marginBottom: 20, fontSize: 13, whiteSpace: 'pre-wrap' }}>
                {dispatcherNotes}
              </div>
            </>
          )}

          {/* Signature */}
          <div style={{ marginTop: 32, borderTop: '1px solid #e5e7eb', paddingTop: 16, display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#6b7280' }}>
            <div>
              <div style={{ marginBottom: 24 }}>Dispatcher Signature: ___________________________</div>
              <div>{dispatcherName || '___________________________'}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div>Date: {new Date(date).toLocaleDateString()}</div>
              <div style={{ marginTop: 4 }}>Shift: {shiftName}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
