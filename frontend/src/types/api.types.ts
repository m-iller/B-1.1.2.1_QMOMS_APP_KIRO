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
  currentState: string
  conflictActive: boolean
  assignedDispatcherId: string | null
  currentZoneId: string | null
  posX: number | null
  posY: number | null
  createdAt: string
}

export interface TelemetryRecord {
  id: string
  machineId: string
  sensorType: string
  normalizedValue: number
  canonicalUnit: string
  timestamp: string
}

export interface Task {
  id: string
  machineId: string
  title: string
  description: string | null
  priority: string
  state: string
  deadline: string
  pendingActivation: boolean
  overdue: boolean
  createdBy: string | null
  createdAt: string
  updatedAt: string
}

export interface HaulCycle {
  id: string
  machineId: string
  originZoneId: string
  destinationZoneId: string
  payloadTonnes: number
  status: string
  immutable: boolean
  startTime: string
  endTime: string | null
  createdAt: string
}

export interface Event {
  id: string
  machineId: string | null
  eventType: string
  payload: Record<string, unknown>
  shiftId: string | null
  expired: boolean
  createdAt: string
}

export interface Zone {
  id: string
  name: string
  description: string | null
  createdAt: string
  updatedAt: string
}

export interface Report {
  id: string
  shiftId: string
  generatedBy: string | null
  data: Record<string, unknown>
  generatedAt: string
}

export interface Notification {
  id: string
  userId: string
  type: string
  payload: Record<string, unknown>
  read: boolean
  shiftId: string | null
  createdAt: string
}
