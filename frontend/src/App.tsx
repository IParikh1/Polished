import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { useAuth } from '@clerk/clerk-react'
import Layout from './components/Layout'
import { ProtectedRoute } from './components/auth'
import LandingPage from './pages/LandingPage'
import BatchDashboard from './pages/BatchDashboard'
import ConsultingPage from './pages/ConsultingPage'
import WritingPage from './pages/WritingPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import PricingPage from './pages/PricingPage'
import AdminPage from './pages/AdminPage'

// Lazy load auth pages to avoid loading Clerk when not needed
const SignInPage = lazy(() => import('./components/auth/SignInPage'))
const SignUpPage = lazy(() => import('./components/auth/SignUpPage'))

const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

// Loading fallback for lazy-loaded components
function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )
}

// Landing page for visitors; signed-in users go straight to the app
function HomeGate() {
  if (!isClerkConfigured) {
    return <LandingPage />
  }
  return <HomeGateWithAuth />
}

function HomeGateWithAuth() {
  const { isLoaded, isSignedIn } = useAuth()

  if (!isLoaded) {
    return <LoadingSpinner />
  }
  if (isSignedIn) {
    return <Navigate to="/batches" replace />
  }
  return <LandingPage />
}

function App() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route path="/" element={<HomeGate />} />

      {/* Public auth routes - lazy loaded */}
      <Route path="/sign-in/*" element={<Suspense fallback={<LoadingSpinner />}><SignInPage /></Suspense>} />
      <Route path="/sign-up/*" element={<Suspense fallback={<LoadingSpinner />}><SignUpPage /></Suspense>} />

      {/* Protected app routes */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
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
        <Route path="admin" element={<AdminPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
