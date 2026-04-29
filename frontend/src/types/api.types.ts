// All field names match the FastAPI snake_case response format exactly

export interface User {
  id: string
  username: string
  role: string
}

export interface LoginResponse {
  access_token: string
  user: User
}

export interface Machine {
  id: string
  name: string
  type: string
  current_state: string
  conflict_active: boolean
  assigned_dispatcher_id: string | null
  current_zone_id: string | null
  pos_x: number | null
  pos_y: number | null
  created_at: string
}

export interface TelemetryRecord {
  id: string
  machine_id: string
  sensor_type: string
  normalized_value: number
  canonical_unit: string
  timestamp: string
}

export interface Task {
  id: string
  machine_id: string
  title: string
  description: string | null
  priority: string
  state: string
  deadline: string
  pending_activation: boolean
  overdue: boolean
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface HaulCycle {
  id: string
  machine_id: string
  origin_zone_id: string
  destination_zone_id: string
  payload_tonnes: number
  status: string
  immutable: boolean
  start_time: string
  end_time: string | null
  created_at: string
}

export interface Event {
  id: string
  machine_id: string | null
  event_type: string
  payload: Record<string, unknown>
  shift_id: string | null
  expired: boolean
  created_at: string
}

export interface Zone {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Report {
  id: string
  shift_id: string
  generated_by: string | null
  data: Record<string, unknown>
  generated_at: string
}

export interface Notification {
  id: string
  user_id: string
  type: string
  payload: Record<string, unknown>
  read: boolean
  shift_id: string | null
  created_at: string
}

// Map module types
export interface AntennaDefinition {
  name: string
  lat: number
  lng: number
}

export interface MapConfig {
  center_lat: number
  center_lng: number
  default_zoom: number
  antennas: AntennaDefinition[]
}

export interface MapConfigRequest {
  center_lat: number
  center_lng: number
  default_zoom: number
  antennas: AntennaDefinition[]
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface ProductionMetrics {
  total_material_tonnes: number
  total_ore_tonnes: number
  total_waste_tonnes: number
  ore_to_waste_ratio: number
  avg_production_rate_tph: number
  peak_production_rate_tph: number
  median_production_rate_tph: number
  planned_production_tonnes: number
  actual_production_tonnes: number
  plan_fulfillment_pct: number
  production_deviation_tonnes: number
  crusher_input_tonnes: number
  stockpile_accumulation_rate_tph: number
  system_throughput_tph: number
  material_per_zone: Record<string, number>
}

export interface FleetMetrics {
  total_machines: number
  active_machines: number
  idle_machines: number
  maintenance_machines: number
  offline_machines: number
  fleet_utilization_pct: number
  avg_machine_utilization_pct: number
  median_machine_utilization_pct: number
  idle_ratio_pct: number
  active_to_idle_ratio: number
  machines_working_vs_assigned_pct: number
  total_breakdown_events: number
  machines_under_repair: number
  avg_repair_time_minutes: number
  total_fleet_downtime_minutes: number
  avg_downtime_per_machine_minutes: number
}

export interface TaskMetrics {
  total_created: number
  completed: number
  in_progress: number
  pending: number
  overdue: number
}

export interface DashboardAnalytics {
  production: ProductionMetrics
  fleet: FleetMetrics
  tasks: TaskMetrics
  shift_id: string | null
  generated_at: string
}
