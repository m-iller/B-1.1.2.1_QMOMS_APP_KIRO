import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import { PermissionsProvider, usePermissions } from './context/PermissionsContext'
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
import { RolesPage } from './pages/Roles/RolesPage'

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

// Guard: redirects to / if user lacks permission for this page
function PageGuard({ page, children }: { page: string; children: React.ReactNode }) {
  const { canAccess, permissions } = usePermissions()
  // Wait until permissions are loaded before guarding
  if (permissions.length === 0) return null
  if (!canAccess(page)) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <PermissionsProvider>
              <NotificationProvider>
                <AppLayout />
              </NotificationProvider>
            </PermissionsProvider>
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/map" element={<PageGuard page="map"><MapViewPage /></PageGuard>} />
        <Route path="/machines/:id" element={<MachineDetailPage />} />
        <Route path="/tasks" element={<PageGuard page="tasks"><TaskPanelPage /></PageGuard>} />
        <Route path="/notifications" element={<PageGuard page="notifications"><NotificationsPage /></PageGuard>} />
        <Route path="/analytics" element={<PageGuard page="analytics"><AnalyticsPage /></PageGuard>} />
        <Route path="/machinery" element={<PageGuard page="machinery"><MachineryPage /></PageGuard>} />
        <Route path="/zones" element={<PageGuard page="zones"><ZonesPage /></PageGuard>} />
        <Route path="/routes" element={<PageGuard page="routes"><RoutesPage /></PageGuard>} />
        <Route path="/roles" element={<PageGuard page="roles"><RolesPage /></PageGuard>} />
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
