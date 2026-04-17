import client from './client'
import type { Notification } from '../types/api.types'

export const getNotifications = (params?: { type?: string; read?: boolean }) =>
  client.get<Notification[]>('/notifications', { params }).then(r => r.data)
export const markNotificationRead = (id: string) =>
  client.patch<Notification>(`/notifications/${id}/read`).then(r => r.data)
