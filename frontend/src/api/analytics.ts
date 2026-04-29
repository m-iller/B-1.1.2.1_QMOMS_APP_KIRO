import client from './client'
import type { DashboardAnalytics } from '../types/api.types'

export const getDashboardAnalytics = () =>
  client.get<DashboardAnalytics>('/analytics/dashboard').then(r => r.data)
