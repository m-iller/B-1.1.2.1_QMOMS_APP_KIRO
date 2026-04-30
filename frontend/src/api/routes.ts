import client from './client'
import type { MachineRoute, Waypoint } from '../types/api.types'

export const getAllRoutes = () =>
  client.get<MachineRoute[]>('/routes').then(r => r.data)

export const getRoutesForMachine = (machineId: string) =>
  client.get<MachineRoute[]>(`/routes/machine/${machineId}`).then(r => r.data)

export const createRoute = (data: {
  machine_id: string
  name: string
  waypoints: Waypoint[]
  color: string
}) => client.post<MachineRoute>('/routes', data).then(r => r.data)

export const updateRoute = (id: string, data: {
  name?: string
  waypoints?: Waypoint[]
  color?: string
}) => client.patch<MachineRoute>(`/routes/${id}`, data).then(r => r.data)

export const deleteRoute = (id: string) => client.delete(`/routes/${id}`)
