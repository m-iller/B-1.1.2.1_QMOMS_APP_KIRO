import type { Notification } from '../../types/api.types'
import { markNotificationRead } from '../../api/notifications'

interface Props { notification: Notification; onRead: () => void }

const TYPE_COLORS: Record<string, string> = {
  alert: '#fee2e2',
  conflict: '#fef3c7',
  system: '#eff6ff',
}

export function NotificationItem({ notification, onRead }: Props) {
  const handleRead = async () => {
    await markNotificationRead(notification.id)
    onRead()
  }

  return (
    <div style={{ background: TYPE_COLORS[notification.type] || '#f9fafb', borderRadius: 6, padding: 12, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <span style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: 11 }}>{notification.type}</span>
        <p style={{ margin: '4px 0 0', fontSize: 13 }}>{JSON.stringify(notification.payload)}</p>
        <p style={{ margin: '2px 0 0', fontSize: 11, color: '#9ca3af' }}>{new Date(notification.created_at).toLocaleString()}</p>
      </div>
      {!notification.read && (
        <button onClick={handleRead} style={{ padding: '4px 10px', fontSize: 12, background: '#fff', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer' }}>
          Mark read
        </button>
      )}
    </div>
  )
}
