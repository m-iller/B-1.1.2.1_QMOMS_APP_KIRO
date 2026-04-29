import { useState, useEffect, useCallback } from 'react'
import { getNotifications, markNotificationRead } from '../../api/notifications'
import { NotificationItem } from './NotificationItem'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Notification } from '../../types/api.types'

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [markingAll, setMarkingAll] = useState(false)

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

  const handleReadAll = async () => {
    setMarkingAll(true)
    try {
      await Promise.all(notifications.map(n => markNotificationRead(n.id)))
      await load()
    } finally {
      setMarkingAll(false)
    }
  }

  const grouped = notifications.reduce<Record<string, Notification[]>>((acc, n) => {
    acc[n.type] = [...(acc[n.type] ?? []), n]
    return acc
  }, {})

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Notifications</h2>
        {notifications.length > 0 && (
          <button
            onClick={handleReadAll}
            disabled={markingAll}
            style={{
              padding: '6px 14px',
              fontSize: 13,
              background: '#f3f4f6',
              color: '#374151',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              cursor: markingAll ? 'not-allowed' : 'pointer',
            }}
          >
            {markingAll ? 'Marking...' : '✓ Read All'}
          </button>
        )}
      </div>
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
