import { usePolling } from '../../hooks/usePolling'
import { getNotifications } from '../../api/notifications'
import { NotificationItem } from './NotificationItem'
import { ErrorBanner } from '../../components/ErrorBanner'

export function NotificationsPage() {
  const { data: notifications, error, loading } = usePolling(() => getNotifications({ read: false }), 7000)

  const grouped = (notifications ?? []).reduce<Record<string, typeof notifications>>((acc, n) => {
    if (!n) return acc
    acc[n.type] = [...(acc[n.type] ?? []), n]
    return acc
  }, {})

  return (
    <div>
      <h2>Notifications</h2>
      <ErrorBanner error={error} />
      {loading && <p>Loading...</p>}
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type}>
          <h4 style={{ textTransform: 'capitalize', marginBottom: 8 }}>{type}</h4>
          {items?.map(n => n && <NotificationItem key={n.id} notification={n} onRead={() => {}} />)}
        </div>
      ))}
      {!loading && (notifications ?? []).length === 0 && <p style={{ color: '#6b7280' }}>No unread notifications</p>}
    </div>
  )
}
