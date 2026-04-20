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
