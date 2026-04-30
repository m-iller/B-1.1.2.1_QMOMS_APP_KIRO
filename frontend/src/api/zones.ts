import client from './client'
import type { Zone } from '../types/api.types'

export const getZones = () => client.get<Zone[]>('/zones').then(r => r.data)

export const createZone = (data: {
  name: string
  description?: string
  zone_type?: string
  color?: string
  center_lat?: number
  center_lng?: number
  radius_meters?: number
}) => client.post<Zone>('/zones', data).then(r => r.data)

export const updateZone = (id: string, data: {
  name?: string
  description?: string
  zone_type?: string
  color?: string
  center_lat?: number
  center_lng?: number
  radius_meters?: number
}) => client.patch<Zone>(`/zones/${id}`, data).then(r => r.data)

export const deleteZone = (id: string) => client.delete(`/zones/${id}`)
