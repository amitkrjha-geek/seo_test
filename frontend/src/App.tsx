import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'
import { useProject } from '@/hooks/use-project'
import { AppShell } from '@/components/layout/app-shell'
import LoginPage from '@/pages/login'
import RegisterPage from '@/pages/register'
import DashboardPage from '@/pages/dashboard'
import NewProjectPage from '@/pages/new-project'
import SettingsPage from '@/pages/settings'
import AuditPage from '@/pages/audit'
import KeywordsPage from '@/pages/keywords'
import CompetitorsPage from '@/pages/competitors'
import BriefPage from '@/pages/brief'
import WritePage from '@/pages/write'
import OptimizePage from '@/pages/optimize'
import TrackPage from '@/pages/track'
import ContentLibraryPage from '@/pages/content-library'
import ReportsPage from '@/pages/reports'
import TeamPage from '@/pages/team'
import StrategyPage from '@/pages/strategy'
import PastArticlesPage from '@/pages/past-articles'
import CalendarPage from '@/pages/calendar'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppInit({ children }: { children: React.ReactNode }) {
  const { loadUser, isAuthenticated } = useAuth()
  const { loadProjects } = useProject()

  useEffect(() => {
    loadUser()
  }, [loadUser])

  useEffect(() => {
    if (isAuthenticated) {
      loadProjects()
    }
  }, [isAuthenticated, loadProjects])

  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppInit>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="projects/new" element={<NewProjectPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="audit" element={<AuditPage />} />
              <Route path="keywords" element={<KeywordsPage />} />
              <Route path="competitors" element={<CompetitorsPage />} />
              <Route path="brief" element={<BriefPage />} />
              <Route path="write" element={<WritePage />} />
              <Route path="optimize" element={<OptimizePage />} />
              <Route path="track" element={<TrackPage />} />
              <Route path="content" element={<ContentLibraryPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="team" element={<TeamPage />} />
              <Route path="strategy" element={<StrategyPage />} />
              <Route path="past-articles" element={<PastArticlesPage />} />
              <Route path="calendar" element={<CalendarPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppInit>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
