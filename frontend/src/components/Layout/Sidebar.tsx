import { NavLink } from 'react-router-dom'
import { useNotifications } from '../../context/NotificationContext'
import { NavBadge } from './NavBadge'
import { useAuth } from '../../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard' },
  { to: '/map', label: 'Map View' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/notifications', label: 'Notifications', badge: true },
]

export function Sidebar() {
  const { unreadCount } = useNotifications()
  const { user, logout } = useAuth()

  return (
    <nav style={{ width: 200, background: '#1e293b', color: '#f1f5f9', minHeight: '100vh', padding: 16, display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 24 }}>⛏ Quarry Monitor</div>
      {NAV_ITEMS.map(item => (
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
