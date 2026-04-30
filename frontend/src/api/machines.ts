import client from './client'
import type { Machine, Conflict } from '../types/api.types'

export const getMachines = () => client.get<Machine[]>('/machines').then(r => r.data)
export const getMachine = (id: string) => client.get<Machine>(`/machines/${id}`).then(r => r.data)
export const createMachine = (data: { name: string; type: string; description?: string; initial_state?: string; enabled_sensors?: string[] }) =>
  client.post<Machine>('/machines', data).then(r => r.data)
export const updateMachineState = (id: string, state: string) =>
  client.patch<Machine>(`/machines/${id}/state`, { state }).then(r => r.data)
export const updateMachineConfig = (id: string, data: { description?: string; enabled_sensors?: string[] }) =>
  client.patch<Machine>(`/machines/${id}/config`, data).then(r => r.data)
export const deleteMachine = (id: string) =>
  client.delete(`/machines/${id}`)
export const getMachineConflicts = (machineId: string) =>
  client.get<Conflict[]>(`/machines/${machineId}/conflicts`).then(r => r.data)
export const resolveConflict = (machineId: string, conflictId: string, resolution: 'dispatcher' | 'operator') =>
  client.post<Machine>(`/machines/${machineId}/conflicts/${conflictId}/resolve`, { resolution }).then(r => r.data)
