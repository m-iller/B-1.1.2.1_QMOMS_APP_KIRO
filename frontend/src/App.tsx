import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import { AppLayout } from './components/Layout/AppLayout'
import { LoginPage } from './pages/Login/LoginPage'
import { DashboardPage } from './pages/Dashboard/DashboardPage'
import { MapViewPage } from './pages/MapView/MapViewPage'
import { MachineDetailPage } from './pages/MachineDetail/MachineDetailPage'
import { TaskPanelPage } from './pages/TaskPanel/TaskPanelPage'
import { NotificationsPage } from './pages/Notifications/NotificationsPage'
import { AnalyticsPage } from './pages/Analytics/AnalyticsPage'
import { MachineryPage } from './pages/Machinery/MachineryPage'
import { ZonesPage } from './pages/Zones/ZonesPage'
import { RoutesPage } from './pages/Routes/RoutesPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  const [checked, setChecked] = useState(false)
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => {
    // Check localStorage synchronously — React state may lag one render behind
    const stored = localStorage.getItem('access_token')
    setHasToken(!!(token || stored))
    setChecked(true)
  }, [token])

  // Wait for the check before rendering anything
  if (!checked) return null

  if (!hasToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <NotificationProvider>
              <AppLayout />
            </NotificationProvider>
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/map" element={<MapViewPage />} />
        <Route path="/machines/:id" element={<MachineDetailPage />} />
        <Route path="/tasks" element={<TaskPanelPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/machinery" element={<MachineryPage />} />
        <Route path="/zones" element={<ZonesPage />} />
        <Route path="/routes" element={<RoutesPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
