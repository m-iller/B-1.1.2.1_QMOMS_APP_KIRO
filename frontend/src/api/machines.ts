import client from './client'
import type { Machine } from '../types/api.types'

export const getMachines = () => client.get<Machine[]>('/machines').then(r => r.data)
export const getMachine = (id: string) => client.get<Machine>(`/machines/${id}`).then(r => r.data)
export const createMachine = (data: { name: string; type: string; initial_state?: string }) =>
  client.post<Machine>('/machines', data).then(r => r.data)
export const updateMachineState = (id: string, state: string) =>
  client.patch<Machine>(`/machines/${id}/state`, { state }).then(r => r.data)
