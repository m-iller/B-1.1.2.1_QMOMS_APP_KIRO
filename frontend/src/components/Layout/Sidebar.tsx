import { NavLink } from 'react-router-dom'
import { useNotifications } from '../../context/NotificationContext'
import { NavBadge } from './NavBadge'
import { useAuth } from '../../context/AuthContext'

const MAP_ROLES = ['dispatcher', 'admin', 'dev']
const TASK_ROLES = ['operator', 'dispatcher', 'manager', 'admin', 'dev']
const NOTIFICATION_ROLES = ['dispatcher', 'admin', 'dev']
const ANALYTICS_ROLES = ['dispatcher', 'admin', 'dev', 'manager']

export function Sidebar() {
  const { unreadCount } = useNotifications()
  const { user, logout } = useAuth()
  const role = user?.role ?? ''

  const navItems = [
    { to: '/', label: 'Dashboard', show: true },
    { to: '/map', label: 'Map View', show: MAP_ROLES.includes(role) },
    { to: '/tasks', label: 'Tasks', show: TASK_ROLES.includes(role) },
    { to: '/analytics', label: 'Analytics', show: ANALYTICS_ROLES.includes(role) },
    { to: '/notifications', label: 'Notifications', badge: true, show: NOTIFICATION_ROLES.includes(role) },
  ].filter(item => item.show)

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
