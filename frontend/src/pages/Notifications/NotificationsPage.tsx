import { useState, useEffect, useCallback } from 'react'
import { getNotifications } from '../../api/notifications'
import { NotificationItem } from './NotificationItem'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Notification } from '../../types/api.types'

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const data = await getNotifications({ read: false })
      setNotifications(data)
      setError(null)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 7000)
    return () => clearInterval(id)
  }, [load])

  const grouped = notifications.reduce<Record<string, Notification[]>>((acc, n) => {
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
          {items.map(n => (
            <NotificationItem key={n.id} notification={n} onRead={load} />
          ))}
        </div>
      ))}
      {!loading && notifications.length === 0 && (
        <p style={{ color: '#6b7280' }}>No unread notifications</p>
      )}
    </div>
  )
}
