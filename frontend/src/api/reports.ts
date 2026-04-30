import client from './client'
import type { Report } from '../types/api.types'

export const getReports = () => client.get<Report[]>('/reports').then(r => r.data)
export const generateReport = (shift_id: string) =>
  client.post<Report>('/reports/generate', { shift_id }).then(r => r.data)

export const getDailyReport = (date: string) =>
  client.get<DailyReport>('/reports/daily', { params: { date } }).then(r => r.data)

export interface DailyReport {
  date: string
  machines: Array<{
    id: string
    name: string
    type: string
    current_state: string
    utilization_pct: number
    state_changes: number
  }>
  haul_cycles: { total: number; completed: number; total_tonnes: number }
  tasks: { total: number; completed: number; pending: number; active: number; overdue: number }
  notifications: Array<{ type: string; payload: Record<string, unknown>; created_at: string }>
  active_machines: number
  total_machines: number
}
