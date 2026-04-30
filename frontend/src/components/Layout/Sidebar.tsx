import { NavLink } from 'react-router-dom'
import { useNotifications } from '../../context/NotificationContext'
import { usePermissions } from '../../context/PermissionsContext'
import { NavBadge } from './NavBadge'
import { useAuth } from '../../context/AuthContext'

const ALL_PAGES = [
  { to: '/',             page: 'dashboard',     label: 'Dashboard',      badge: false },
  { to: '/map',          page: 'map',           label: 'Map View',       badge: false },
  { to: '/tasks',        page: 'tasks',         label: 'Tasks',          badge: false },
  { to: '/analytics',    page: 'analytics',     label: 'Analytics',      badge: false },
  { to: '/machinery',    page: 'machinery',     label: 'Machinery',      badge: false },
  { to: '/zones',        page: 'zones',         label: 'Zones',          badge: false },
  { to: '/routes',       page: 'routes',        label: 'Routes',         badge: false },
  { to: '/notifications',page: 'notifications', label: 'Notifications',  badge: true  },
  { to: '/roles',        page: 'roles',         label: 'Roles',          badge: false },
  { to: '/shift-report', page: 'shift_report',  label: 'Shift Report',   badge: false },
]

export function Sidebar() {
  const { unreadCount } = useNotifications()
  const { user, logout } = useAuth()
  const { canAccess } = usePermissions()

  const navItems = ALL_PAGES.filter(item =>
    item.page === 'dashboard' || canAccess(item.page)
  )

  return (
    <nav style={{ width: 200, background: '#1e293b', color: '#f1f5f9', minHeight: '100vh', padding: 16, display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 24 }}>⛏ Quarry Monitor</div>
      {navItems.map(item => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          style={({ isActive }) => ({
            display: 'block', padding: '8px 12px', borderRadius: 6, marginBottom: 4,
            color: isActive ? '#fff' : '#94a3b8',
            background: isActive ? '#334155' : 'transparent',
            textDecoration: 'none',
          })}
        >
          {item.label}
          {item.badge && <NavBadge count={unreadCount} />}
        </NavLink>
      ))}
      <div style={{ marginTop: 'auto', fontSize: 13, color: '#64748b' }}>
        <div>{user?.username} ({user?.role})</div>
        <button onClick={logout} style={{ marginTop: 8, background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0 }}>Logout</button>
      </div>
    </nav>
  )
}
