import React, { createContext, useContext, useState, useEffect } from 'react'
import { getNotifications } from '../api/notifications'

interface NotificationContextValue {
  unreadCount: number
  refresh: () => void
}

const NotificationContext = createContext<NotificationContextValue>({ unreadCount: 0, refresh: () => {} })

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0)

  const refresh = async () => {
    try {
      const notifs = await getNotifications({ read: false })
      setUnreadCount(notifs.length)
    } catch {
      // ignore — don't crash on polling errors
    }
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 7000)
    return () => clearInterval(id)
  }, [])

  return <NotificationContext.Provider value={{ unreadCount, refresh }}>{children}</NotificationContext.Provider>
}

export function useNotifications() {
  return useContext(NotificationContext)
}
