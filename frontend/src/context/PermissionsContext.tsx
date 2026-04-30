import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getRolePermissions, type RolePermission } from '../api/rolePermissions'
import { useAuth } from './AuthContext'

interface PermissionsContextValue {
  permissions: RolePermission[]
  canAccess: (page: string) => boolean
  canDo: (privilege: string) => boolean
  refresh: () => void
}

const PermissionsContext = createContext<PermissionsContextValue>({
  permissions: [],
  canAccess: () => true,
  canDo: () => true,
  refresh: () => {},
})

export function PermissionsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const [permissions, setPermissions] = useState<RolePermission[]>([])

  const refresh = useCallback(async () => {
    try {
      const data = await getRolePermissions()
      setPermissions(data)
    } catch {
      // If fetch fails, fall back to allowing all (graceful degradation)
    }
  }, [])

  useEffect(() => {
    if (user) refresh()
  }, [user, refresh])

  const canAccess = useCallback((page: string): boolean => {
    if (!user) return false
    const rolePerms = permissions.find(p => p.role === user.role)
    if (!rolePerms) return true
    return rolePerms.pages.includes(page)
  }, [user, permissions])

  const canDo = useCallback((privilege: string): boolean => {
    if (!user) return false
    const rolePerms = permissions.find(p => p.role === user.role)
    if (!rolePerms) return true
    return rolePerms.pages.includes(privilege)
  }, [user, permissions])

  return (
    <PermissionsContext.Provider value={{ permissions, canAccess, canDo, refresh }}>
      {children}
    </PermissionsContext.Provider>
  )
}

export function usePermissions() {
  return useContext(PermissionsContext)
}
