import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Layout from './components/Layout'
import { ProtectedRoute } from './components/auth'
import BatchDashboard from './pages/BatchDashboard'
import ConsultingPage from './pages/ConsultingPage'
import WritingPage from './pages/WritingPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import PricingPage from './pages/PricingPage'

// Lazy load auth pages to avoid loading Clerk when not needed
const SignInPage = lazy(() => import('./components/auth/SignInPage'))
const SignUpPage = lazy(() => import('./components/auth/SignUpPage'))

// Loading fallback for lazy-loaded components
function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )
}

function App() {
  return (
    <Routes>
      {/* Public auth routes - lazy loaded */}
      <Route path="/sign-in/*" element={<Suspense fallback={<LoadingSpinner />}><SignInPage /></Suspense>} />
      <Route path="/sign-up/*" element={<Suspense fallback={<LoadingSpinner />}><SignUpPage /></Suspense>} />

      {/* Protected app routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/batches" replace />} />
        <Route path="batches" element={<BatchDashboard />} />
        <Route path="batches/:batchId" element={<BatchDashboard />} />
        <Route path="consulting" element={<ConsultingPage />} />
        <Route path="consulting/:sessionId" element={<ConsultingPage />} />
        <Route path="writing" element={<WritingPage />} />
        <Route path="writing/:batchId/:resumeId" element={<WritingPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="help" element={<HelpPage />} />
      </Route>
    </Routes>
  )
}

export default App
