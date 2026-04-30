import { useState, useCallback, useEffect } from 'react'
import {
  getRolePermissions,
  createRolePermission,
  updateRolePermission,
  deleteRolePermission,
  type RolePermission,
} from '../../api/rolePermissions'
import { usePermissions } from '../../context/PermissionsContext'
import { ErrorBanner } from '../../components/ErrorBanner'

const ALL_PAGES = [
  { id: 'dashboard',     label: 'Dashboard' },
  { id: 'map',           label: 'Map View' },
  { id: 'tasks',         label: 'Tasks' },
  { id: 'analytics',     label: 'Analytics' },
  { id: 'machinery',     label: 'Machinery' },
  { id: 'zones',         label: 'Zones' },
  { id: 'routes',        label: 'Routes' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'roles',         label: 'Roles (this page)' },
]

const PROTECTED_ROLES = new Set(['dev', 'admin', 'dispatcher', 'operator'])

export function RolesPage() {
  const { refresh: refreshPermissions } = usePermissions()
  const [roles, setRoles] = useState<RolePermission[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  // New role form
  const [newRole, setNewRole] = useState('')
  const [newPages, setNewPages] = useState<string[]>(['dashboard'])
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Edit state: role -> pages[]
  const [editPages, setEditPages] = useState<Record<string, string[]>>({})
  const [savingRole, setSavingRole] = useState<string | null>(null)
  const [deletingRole, setDeletingRole] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await getRolePermissions()
      setRoles(data)
      setEditPages(Object.fromEntries(data.map(r => [r.role, [...r.pages]])))
      setError(null)
    } catch (e) { setError(e) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const togglePage = (role: string, page: string) => {
    setEditPages(prev => {
      const current = prev[role] ?? []
      const updated = current.includes(page)
        ? current.filter(p => p !== page)
        : [...current, page]
      return { ...prev, [role]: updated }
    })
  }

  const toggleNewPage = (page: string) => {
    setNewPages(prev =>
      prev.includes(page) ? prev.filter(p => p !== page) : [...prev, page]
    )
  }

  const isDirty = (role: RolePermission) => {
    const current = editPages[role.role] ?? role.pages
    return JSON.stringify([...current].sort()) !== JSON.stringify([...role.pages].sort())
  }

  const handleSave = async (role: string) => {
    setSavingRole(role)
    try {
      await updateRolePermission(role, editPages[role] ?? [])
      await load()
      refreshPermissions()
    } finally { setSavingRole(null) }
  }

  const handleDelete = async (role: string) => {
    setDeletingRole(role)
    try {
      await deleteRolePermission(role)
      await load()
      refreshPermissions()
    } catch (err: any) {
      alert(err?.response?.data?.detail ?? 'Failed to delete role')
    } finally { setDeletingRole(null) }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newRole.trim()) return
    setCreating(true); setCreateError('')
    try {
      await createRolePermission({ role: newRole.trim().toLowerCase(), pages: newPages })
      setNewRole('')
      setNewPages(['dashboard'])
      await load()
      refreshPermissions()
    } catch (err: any) {
      setCreateError(err?.response?.data?.detail ?? 'Failed to create role')
    } finally { setCreating(false) }
  }

  return (
    <div>
      <h2>Role Permissions</h2>
      <p style={{ color: '#6b7280', fontSize: 13, marginBottom: 20 }}>
        Control which pages each role can access. Changes take effect immediately for all users with that role.
      </p>
      <ErrorBanner error={error} />

      {/* Create new role */}
      <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 24 }}>
        <h4 style={{ margin: '0 0 12px' }}>Create New Role</h4>
        <form onSubmit={handleCreate}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', marginBottom: 12 }}>
            <label style={{ fontSize: 13, flex: 1 }}>
              Role Name
              <input
                value={newRole}
                onChange={e => setNewRole(e.target.value)}
                placeholder="e.g. supervisor"
                required
                style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13 }}
              />
            </label>
          </div>
          <div style={{ fontSize: 13, marginBottom: 10 }}>
            <strong>Pages:</strong>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
              {ALL_PAGES.map(p => (
                <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, cursor: 'pointer' }}>
                  <input type="checkbox" checked={newPages.includes(p.id)} onChange={() => toggleNewPage(p.id)} />
                  {p.label}
                </label>
              ))}
            </div>
          </div>
          {createError && <p style={{ color: '#dc2626', fontSize: 12, margin: '0 0 8px' }}>{createError}</p>}
          <button type="submit" disabled={creating} style={{ padding: '6px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
            {creating ? 'Creating...' : '+ Create Role'}
          </button>
        </form>
      </div>

      {/* Role list */}
      {loading && <p style={{ color: '#6b7280' }}>Loading...</p>}

      {roles.map(role => {
        const pages = editPages[role.role] ?? role.pages
        const dirty = isDirty(role)
        const isProtected = PROTECTED_ROLES.has(role.role)

        return (
          <div key={role.role} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 12, background: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <strong style={{ fontSize: 15 }}>{role.role}</strong>
                {isProtected && (
                  <span style={{ fontSize: 10, background: '#fef3c7', color: '#92400e', padding: '1px 6px', borderRadius: 3 }}>built-in</span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {dirty && (
                  <button
                    onClick={() => handleSave(role.role)}
                    disabled={savingRole === role.role}
                    style={{ padding: '4px 12px', fontSize: 12, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                  >
                    {savingRole === role.role ? 'Saving...' : 'Save'}
                  </button>
                )}
                {dirty && (
                  <button
                    onClick={() => setEditPages(prev => ({ ...prev, [role.role]: [...role.pages] }))}
                    style={{ padding: '4px 10px', fontSize: 12, background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer' }}
                  >
                    Reset
                  </button>
                )}
                {!isProtected && (
                  <button
                    onClick={() => handleDelete(role.role)}
                    disabled={deletingRole === role.role}
                    style={{ padding: '4px 10px', fontSize: 12, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}
                  >
                    {deletingRole === role.role ? '...' : 'Delete'}
                  </button>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {ALL_PAGES.map(p => (
                <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={pages.includes(p.id)}
                    onChange={() => togglePage(role.role, p.id)}
                  />
                  <span style={{ color: pages.includes(p.id) ? '#111827' : '#9ca3af' }}>{p.label}</span>
                </label>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
