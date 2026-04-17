import client from './client'
import type { Report } from '../types/api.types'

export const getReports = () => client.get<Report[]>('/reports').then(r => r.data)
export const generateReport = (shift_id: string) =>
  client.post<Report>('/reports/generate', { shift_id }).then(r => r.data)
