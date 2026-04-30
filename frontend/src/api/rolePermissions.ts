import client from './client'

export interface RolePermission {
  id: string
  role: string
  pages: string[]
  created_at: string
  updated_at: string
}

export const getRolePermissions = () =>
  client.get<RolePermission[]>('/role-permissions').then(r => r.data)

export const createRolePermission = (data: { role: string; pages: string[] }) =>
  client.post<RolePermission>('/role-permissions', data).then(r => r.data)

export const updateRolePermission = (role: string, pages: string[]) =>
  client.patch<RolePermission>(`/role-permissions/${role}`, { pages }).then(r => r.data)

export const deleteRolePermission = (role: string) =>
  client.delete(`/role-permissions/${role}`)
