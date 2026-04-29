"""
Analytics service — computes all dashboard metrics.
Fields marked [simulated] use estimation where real data is unavailable.
"""
import statistics
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics import repository
from app.modules.analytics.schemas import (
    DashboardAnalytics,
    FleetMetrics,
    ProductionMetrics,
    TaskMetrics,
)

# ---------------------------------------------------------------------------
# Simulation constants (clearly named, not magic numbers)
# ---------------------------------------------------------------------------

# Fraction of total haul payload classified as ore vs waste [simulated]
ORE_FRACTION = 0.65
WASTE_FRACTION = 0.35

# Planned production per shift in tonnes [simulated — no planning module]
PLANNED_PRODUCTION_TONNES = 5000.0

# Fraction of haul payload assumed to go to crusher [simulated]
CRUSHER_INPUT_FRACTION = 0.4

# Assumed shift duration in hours for rate calculations
SHIFT_DURATION_HOURS = 8.0

# Assumed average repair time in minutes [simulated — no repair log]
SIMULATED_AVG_REPAIR_MINUTES = 45.0

# Telemetry recency window for "online" detection (minutes)
TELEMETRY_ONLINE_WINDOW_MINUTES = 30


async def compute_dashboard(db: AsyncSession) -> DashboardAnalytics:
    production = await _compute_production(db)
    fleet = await _compute_fleet(db)
    tasks = await _compute_tasks(db)

    return DashboardAnalytics(
        production=production,
        fleet=fleet,
        tasks=tasks,
        shift_id=None,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


async def _compute_production(db: AsyncSession) -> ProductionMetrics:
    haul_cycles = await repository.get_completed_haul_cycles(db)
    zone_names = await repository.get_zone_names(db)

    payload_values = [hc.payload_tonnes for hc in haul_cycles]
    total_material = sum(payload_values)

    # Ore/waste split [simulated]
    total_ore = total_material * ORE_FRACTION
    total_waste = total_material * WASTE_FRACTION
    ore_to_waste = (total_ore / total_waste) if total_waste > 0 else 0.0

    # Production rates from individual haul cycle payloads
    # Each cycle duration estimated from start/end times where available
    cycle_rates: list[float] = []
    for hc in haul_cycles:
        if hc.start_time and hc.end_time:
            duration_hours = (hc.end_time - hc.start_time).total_seconds() / 3600
            if duration_hours > 0:
                cycle_rates.append(hc.payload_tonnes / duration_hours)

    avg_rate = statistics.mean(cycle_rates) if cycle_rates else 0.0
    peak_rate = max(cycle_rates) if cycle_rates else 0.0
    median_rate = statistics.median(cycle_rates) if cycle_rates else 0.0

    # System throughput over assumed shift duration
    system_throughput = total_material / SHIFT_DURATION_HOURS if SHIFT_DURATION_HOURS > 0 else 0.0

    # Plan fulfillment [simulated planned value]
    plan_fulfillment = (total_material / PLANNED_PRODUCTION_TONNES * 100) if PLANNED_PRODUCTION_TONNES > 0 else 0.0
    production_deviation = total_material - PLANNED_PRODUCTION_TONNES

    # Crusher input [simulated as fraction of total]
    crusher_input = total_material * CRUSHER_INPUT_FRACTION

    # Stockpile accumulation rate [simulated]
    stockpile_rate = (total_material * (1 - CRUSHER_INPUT_FRACTION)) / SHIFT_DURATION_HOURS

    # Material per zone — combine origin and destination
    origin_map = await repository.get_haul_cycles_by_origin(db)
    dest_map = await repository.get_haul_cycles_by_destination(db)
    all_zone_ids = set(origin_map) | set(dest_map)
    material_per_zone: dict[str, float] = {
        zone_names.get(zone_id, zone_id): origin_map.get(zone_id, 0.0) + dest_map.get(zone_id, 0.0)
        for zone_id in all_zone_ids
    }

    return ProductionMetrics(
        total_material_tonnes=round(total_material, 2),
        total_ore_tonnes=round(total_ore, 2),
        total_waste_tonnes=round(total_waste, 2),
        ore_to_waste_ratio=round(ore_to_waste, 3),
        avg_production_rate_tph=round(avg_rate, 2),
        peak_production_rate_tph=round(peak_rate, 2),
        median_production_rate_tph=round(median_rate, 2),
        planned_production_tonnes=PLANNED_PRODUCTION_TONNES,
        actual_production_tonnes=round(total_material, 2),
        plan_fulfillment_pct=round(plan_fulfillment, 1),
        production_deviation_tonnes=round(production_deviation, 2),
        crusher_input_tonnes=round(crusher_input, 2),
        stockpile_accumulation_rate_tph=round(stockpile_rate, 2),
        system_throughput_tph=round(system_throughput, 2),
        material_per_zone=material_per_zone,
    )


async def _compute_fleet(db: AsyncSession) -> FleetMetrics:
    machines = await repository.get_all_machines(db)
    total_machines = len(machines)

    state_counts = await repository.get_machine_state_counts(db)
    active_count = state_counts.get("operating", 0)
    idle_count = state_counts.get("idle", 0)
    maintenance_count = state_counts.get("maintenance", 0)
    breakdown_count = state_counts.get("breakdown", 0)

    # Offline = machines with no recent telemetry [simulated via telemetry recency]
    online_machine_ids = await repository.get_machines_with_recent_telemetry(
        db, within_minutes=TELEMETRY_ONLINE_WINDOW_MINUTES
    )
    offline_count = sum(1 for m in machines if m.id not in online_machine_ids)

    # Fleet utilization = active / (total - offline)
    available = total_machines - offline_count
    fleet_utilization = (active_count / available * 100) if available > 0 else 0.0

    # Per-machine utilization
    utilization_map = await repository.get_utilization_per_machine(db)
    utilization_values = list(utilization_map.values())
    avg_utilization = statistics.mean(utilization_values) if utilization_values else 0.0
    median_utilization = statistics.median(utilization_values) if utilization_values else 0.0

    idle_ratio = (idle_count / total_machines * 100) if total_machines > 0 else 0.0
    active_to_idle = (active_count / idle_count) if idle_count > 0 else float(active_count)

    # Machines working vs assigned (assigned = has dispatcher)
    assigned_machines = [m for m in machines if m.assigned_dispatcher_id is not None]
    working_assigned = sum(
        1 for m in assigned_machines if m.current_state == "operating"
    )
    working_vs_assigned = (
        (working_assigned / len(assigned_machines) * 100) if assigned_machines else 0.0
    )

    total_breakdowns = await repository.count_breakdown_events(db)
    machines_under_repair = breakdown_count + maintenance_count

    # Downtime estimation [simulated — no repair log]
    avg_repair_minutes = SIMULATED_AVG_REPAIR_MINUTES
    total_downtime = machines_under_repair * avg_repair_minutes
    avg_downtime_per_machine = (total_downtime / total_machines) if total_machines > 0 else 0.0

    return FleetMetrics(
        total_machines=total_machines,
        active_machines=active_count,
        idle_machines=idle_count,
        maintenance_machines=maintenance_count,
        offline_machines=offline_count,
        fleet_utilization_pct=round(fleet_utilization, 1),
        avg_machine_utilization_pct=round(avg_utilization, 1),
        median_machine_utilization_pct=round(median_utilization, 1),
        idle_ratio_pct=round(idle_ratio, 1),
        active_to_idle_ratio=round(active_to_idle, 2),
        machines_working_vs_assigned_pct=round(working_vs_assigned, 1),
        total_breakdown_events=total_breakdowns,
        machines_under_repair=machines_under_repair,
        avg_repair_time_minutes=avg_repair_minutes,
        total_fleet_downtime_minutes=round(total_downtime, 1),
        avg_downtime_per_machine_minutes=round(avg_downtime_per_machine, 1),
    )


async def _compute_tasks(db: AsyncSession) -> TaskMetrics:
    state_counts = await repository.get_task_counts(db)
    overdue = await repository.count_overdue_tasks(db)

    total = sum(state_counts.values())
    completed = state_counts.get("completed", 0) + state_counts.get("validated", 0)
    in_progress = state_counts.get("active", 0)
    pending = state_counts.get("pending", 0)

    return TaskMetrics(
        total_created=total,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        overdue=overdue,
    )
