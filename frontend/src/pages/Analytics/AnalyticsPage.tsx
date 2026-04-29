import { usePolling } from '../../hooks/usePolling'
import { getDashboardAnalytics } from '../../api/analytics'
import { ErrorBanner } from '../../components/ErrorBanner'
import { MetricCard } from './MetricCard'
import { MetricSection } from './MetricSection'

export function AnalyticsPage() {
  const { data, error, loading } = usePolling(getDashboardAnalytics, 15000)

  if (loading && !data) return <div style={{ padding: 24, color: '#6b7280' }}>Loading analytics...</div>

  const p = data?.production
  const f = data?.fleet
  const t = data?.tasks

  const fulfillmentHighlight = p
    ? p.plan_fulfillment_pct >= 90 ? 'good' : p.plan_fulfillment_pct >= 70 ? 'warn' : 'bad'
    : 'neutral'

  const fleetHighlight = f
    ? f.fleet_utilization_pct >= 70 ? 'good' : f.fleet_utilization_pct >= 40 ? 'warn' : 'bad'
    : 'neutral'

  return (
    <div style={{ padding: '0 0 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>Analytics Dashboard</h2>
        {data && (
          <span style={{ fontSize: 12, color: '#9ca3af' }}>
            Updated {new Date(data.generated_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      <ErrorBanner error={error} />

      {p && (
        <>
          <MetricSection title="Production — Material">
            <MetricCard label="Total Material Mined" value={p.total_material_tonnes} unit="t" />
            <MetricCard label="Total Ore Mined" value={p.total_ore_tonnes} unit="t" simulated />
            <MetricCard label="Total Waste Removed" value={p.total_waste_tonnes} unit="t" simulated />
            <MetricCard label="Ore-to-Waste Ratio" value={p.ore_to_waste_ratio} simulated />
            <MetricCard label="Crusher Input Volume" value={p.crusher_input_tonnes} unit="t" simulated />
            <MetricCard label="Stockpile Accumulation" value={p.stockpile_accumulation_rate_tph} unit="t/h" simulated />
            <MetricCard label="System Throughput" value={p.system_throughput_tph} unit="t/h" />
          </MetricSection>

          <MetricSection title="Production — Rates">
            <MetricCard label="Avg Production Rate" value={p.avg_production_rate_tph} unit="t/h" />
            <MetricCard label="Peak Production Rate" value={p.peak_production_rate_tph} unit="t/h" />
            <MetricCard label="Median Production Rate" value={p.median_production_rate_tph} unit="t/h" />
          </MetricSection>

          <MetricSection title="Production vs Plan">
            <MetricCard label="Planned Production" value={p.planned_production_tonnes} unit="t" simulated />
            <MetricCard label="Actual Production" value={p.actual_production_tonnes} unit="t" />
            <MetricCard label="Plan Fulfillment" value={`${p.plan_fulfillment_pct}%`} highlight={fulfillmentHighlight} simulated />
            <MetricCard
              label="Deviation from Plan"
              value={p.production_deviation_tonnes >= 0 ? `+${p.production_deviation_tonnes}` : p.production_deviation_tonnes}
              unit="t"
              highlight={p.production_deviation_tonnes >= 0 ? 'good' : 'bad'}
              simulated
            />
          </MetricSection>

          {Object.keys(p.material_per_zone).length > 0 && (
            <MetricSection title="Material per Zone">
              {Object.entries(p.material_per_zone).map(([zone, tonnes]) => (
                <MetricCard key={zone} label={zone} value={Math.round(tonnes)} unit="t" />
              ))}
            </MetricSection>
          )}
        </>
      )}

      {f && (
        <>
          <MetricSection title="Fleet — Status">
            <MetricCard label="Total Machines" value={f.total_machines} />
            <MetricCard label="Active (Operating)" value={f.active_machines} highlight="good" />
            <MetricCard label="Idle" value={f.idle_machines} highlight="warn" />
            <MetricCard label="Under Maintenance" value={f.maintenance_machines} highlight="warn" />
            <MetricCard label="Offline (No Telemetry)" value={f.offline_machines} highlight={f.offline_machines > 0 ? 'bad' : 'neutral'} simulated />
          </MetricSection>

          <MetricSection title="Fleet — Utilization">
            <MetricCard label="Fleet Utilization" value={`${f.fleet_utilization_pct}%`} highlight={fleetHighlight} />
            <MetricCard label="Avg Machine Utilization" value={`${f.avg_machine_utilization_pct}%`} />
            <MetricCard label="Median Machine Utilization" value={`${f.median_machine_utilization_pct}%`} />
            <MetricCard label="Idle Ratio" value={`${f.idle_ratio_pct}%`} highlight={f.idle_ratio_pct > 50 ? 'bad' : 'neutral'} />
            <MetricCard label="Active-to-Idle Ratio" value={f.active_to_idle_ratio} />
            <MetricCard label="Working vs Assigned" value={`${f.machines_working_vs_assigned_pct}%`} />
          </MetricSection>

          <MetricSection title="Fleet — Downtime & Repairs">
            <MetricCard label="Total Breakdown Events" value={f.total_breakdown_events} highlight={f.total_breakdown_events > 0 ? 'bad' : 'good'} />
            <MetricCard label="Machines Under Repair" value={f.machines_under_repair} highlight={f.machines_under_repair > 0 ? 'warn' : 'neutral'} />
            <MetricCard label="Avg Repair Time" value={f.avg_repair_time_minutes} unit="min" simulated />
            <MetricCard label="Total Fleet Downtime" value={f.total_fleet_downtime_minutes} unit="min" simulated />
            <MetricCard label="Avg Downtime / Machine" value={f.avg_downtime_per_machine_minutes} unit="min" simulated />
          </MetricSection>
        </>
      )}

      {t && (
        <MetricSection title="Tasks">
          <MetricCard label="Total Created" value={t.total_created} />
          <MetricCard label="Completed" value={t.completed} highlight="good" />
          <MetricCard label="In Progress" value={t.in_progress} highlight="warn" />
          <MetricCard label="Pending" value={t.pending} />
          <MetricCard label="Overdue" value={t.overdue} highlight={t.overdue > 0 ? 'bad' : 'neutral'} />
        </MetricSection>
      )}

      <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 8 }}>
        Fields marked <em>simulated</em> are estimated where real data is unavailable (ore/waste split, planned production, repair times).
      </p>
    </div>
  )
}
