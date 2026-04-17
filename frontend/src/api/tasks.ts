import client from './client'
import type { Task } from '../types/api.types'

export const getTasks = (params?: { machine_id?: string; state?: string }) =>
  client.get<Task[]>('/tasks', { params }).then(r => r.data)
export const createTask = (data: { machine_id: string; title: string; description?: string; priority: string; deadline: string }) =>
  client.post<Task>('/tasks', data).then(r => r.data)
export const updateTask = (id: string, data: { state: string }) =>
  client.patch<Task>(`/tasks/${id}`, data).then(r => r.data)
export const confirmTaskActivation = (id: string) =>
  client.post<Task>(`/tasks/${id}/confirm-activation`).then(r => r.data)
