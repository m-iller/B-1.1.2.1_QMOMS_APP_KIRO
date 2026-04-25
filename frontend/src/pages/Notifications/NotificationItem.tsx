import { useState } from 'react'
import type { Notification } from '../../types/api.types'
import { markNotificationRead } from '../../api/notifications'

interface Props { notification: Notification; onRead: () => void }

const TYPE_COLORS: Record<string, { bg: string; border: string }> = {
  alert:    { bg: '#fee2e2', border: '#fca5a5' },
  conflict: { bg: '#fef3c7', border: '#fcd34d' },
  system:   { bg: '#eff6ff', border: '#93c5fd' },
}

export function NotificationItem({ notification, onRead }: Props) {
  const [expanded, setExpanded] = useState(false)

  const p = notification.payload as {
    name?: string
    desc?: string
    bigdesc?: string
    date?: string
    timestamp?: string
  }

  const colors = TYPE_COLORS[notification.type] ?? { bg: '#f9fafb', border: '#e5e7eb' }

  const handleRead = async () => {
    await markNotificationRead(notification.id)
    onRead()
  }

  return (
    <div style={{
      background: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 6,
      padding: '10px 12px',
      marginBottom: 8,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: 13 }}>{p.name ?? notification.type}</span>
            <span style={{
              fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
              background: colors.border, borderRadius: 3, padding: '1px 5px',
            }}>
              {notification.type}
            </span>
          </div>
          {p.desc && (
            <p style={{ margin: '3px 0 0', fontSize: 13, color: '#374151' }}>{p.desc}</p>
          )}
          <p style={{ margin: '2px 0 0', fontSize: 11, color: '#9ca3af' }}>
            {p.date && <span>{p.date} · </span>}
            {new Date(p.timestamp ?? notification.created_at).toLocaleTimeString()}
          </p>
        </div>

        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {p.bigdesc && (
            <button
              onClick={() => setExpanded(e => !e)}
              style={{ padding: '3px 8px', fontSize: 11, background: '#fff', border: `1px solid ${colors.border}`, borderRadius: 4, cursor: 'pointer' }}
            >
              {expanded ? '▲ Less' : '▼ More'}
            </button>
          )}
          {!notification.read && (
            <button
              onClick={handleRead}
              style={{ padding: '3px 8px', fontSize: 11, background: '#fff', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer' }}
            >
              ✓ Read
            </button>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && p.bigdesc && (
        <div style={{
          marginTop: 8, padding: '8px 10px',
          background: 'rgba(255,255,255,0.6)', borderRadius: 4,
          fontSize: 13, color: '#1f2937', whiteSpace: 'pre-wrap',
        }}>
          {p.bigdesc}
        </div>
      )}
    </div>
  )
}
