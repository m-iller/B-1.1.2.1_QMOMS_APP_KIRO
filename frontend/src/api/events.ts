import client from './client'
import type { Event } from '../types/api.types'

export const getEvents = (params?: Record<string, string>) =>
  client.get<Event[]>('/events', { params }).then(r => r.data)
