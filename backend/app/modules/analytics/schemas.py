"""
Analytics dashboard schemas.
Fields marked [simulated] are derived/estimated where real data is unavailable.
"""
from pydantic import BaseModel


class ProductionMetrics(BaseModel):
    total_material_tonnes: float
    total_ore_tonnes: float           # [simulated] 65% of haul payload
    total_waste_tonnes: float         # [simulated] 35% of haul payload
    ore_to_waste_ratio: float         # [simulated]
    avg_production_rate_tph: float    # tonnes per hour
    peak_production_rate_tph: float
    median_production_rate_tph: float
    planned_production_tonnes: float  # [simulated] configurable constant
    actual_production_tonnes: float
    plan_fulfillment_pct: float
    production_deviation_tonnes: float
    crusher_input_tonnes: float       # [simulated] haul cycles to crusher zone
    stockpile_accumulation_rate_tph: float  # [simulated]
    system_throughput_tph: float
    material_per_zone: dict[str, float]     # zone_name -> tonnes


class FleetMetrics(BaseModel):
    total_machines: int
    active_machines: int
    idle_machines: int
    maintenance_machines: int
    offline_machines: int             # no telemetry in last 30 min [simulated]
    fleet_utilization_pct: float
    avg_machine_utilization_pct: float
    median_machine_utilization_pct: float
    idle_ratio_pct: float
    active_to_idle_ratio: float
    machines_working_vs_assigned_pct: float
    total_breakdown_events: int
    machines_under_repair: int
    avg_repair_time_minutes: float    # [simulated] from breakdown→maintenance transitions
    total_fleet_downtime_minutes: float  # [simulated]
    avg_downtime_per_machine_minutes: float  # [simulated]


class TaskMetrics(BaseModel):
    total_created: int
    completed: int
    in_progress: int
    pending: int
    overdue: int


class DashboardAnalytics(BaseModel):
    production: ProductionMetrics
    fleet: FleetMetrics
    tasks: TaskMetrics
    shift_id: str | None
    generated_at: str
